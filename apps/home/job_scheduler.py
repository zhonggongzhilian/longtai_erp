from datetime import datetime, timedelta

from django.utils import timezone

from .models import Device, Order, Process, Task, Product


def is_max_process(order_product):
    """
    判断当前工序是否是订单产品的最大工序。
    """
    all_processes = Process.objects.filter(product_code=order_product.product_code).order_by('process_i')
    process_indices = [p.process_i for p in all_processes]
    max_process_i = max(process_indices)
    return order_product.cur_process_i == max_process_i


def has_process(order_product):
    """
    检查订单产品是否有对应的工序。
    """
    return Process.objects.filter(
        product_code=order_product.product_code,
        process_i__gt=order_product.cur_process_i
    ).exists()


def remove_order_products_with_outside_process(order_products):
    """
    遍历 order_products，检查每个工序的设备名称是否存在于设备列表中，
    如果不存在则添加设备，并移除具有 is_outside 值为 1 的工序的订单产品。
    """
    # 获取现有设备名称的集合
    existing_device_names = set(Device.objects.values_list('device_name', flat=True))

    to_remove = []

    for order_product in order_products:
        # 查找当前订单产品的所有工序
        processes = Process.objects.filter(
            product_code=order_product.product_code,
            process_i__gt=order_product.cur_process_i
        )

        for process in processes:
            device_name = process.device_name

            # 如果工序的设备名称不在现有设备名称集合中，添加新设备
            if device_name not in existing_device_names:
                # 添加新设备到数据库
                Device.objects.create(
                    device_name=device_name
                )

            # 如果工序的 is_outside 值为 1，标记订单产品进行移除
            if process.is_outside == 1:
                to_remove.append(order_product)
                break  # 一旦找到一个 is_outside 为 1 的工序，停止进一步检查

    # 从 order_products 列表中移除标记的订单产品
    for order_product in to_remove:
        order_products.remove(order_product)


def add_working_time(start_time, duration=0):
    """增加工作时间，跳过非工作时间"""

    end_time = start_time

    while duration >= 0:
        work_start_morning = end_time.replace(hour=9, minute=0, second=0, microsecond=0)
        work_end_morning = end_time.replace(hour=12, minute=0, second=0, microsecond=0)
        work_start_afternoon = end_time.replace(hour=13, minute=0, second=0, microsecond=0)
        work_end_afternoon = end_time.replace(hour=18, minute=0, second=0, microsecond=0)

        if end_time < work_start_morning:
            end_time = work_start_morning
        elif end_time < work_end_morning:
            available_time = (work_end_morning - end_time).seconds / 60
            if duration <= available_time:
                end_time += timedelta(minutes=duration)
                duration = -1
            else:
                duration -= available_time
                end_time = work_start_afternoon
        elif end_time < work_start_afternoon:
            end_time = work_start_afternoon
        elif end_time < work_end_afternoon:
            available_time = (work_end_afternoon - end_time).seconds / 60
            if duration <= available_time:
                end_time += timedelta(minutes=duration)
                duration = -1
            else:
                duration -= available_time
                end_time = work_start_morning + timedelta(days=1)
        else:
            # 处理结束时间在下午工作结束后的情况
            end_time = work_start_morning + timedelta(days=1)

    return end_time


def schedule_production(start_date_str='2024-01-01'):
    # 清空 Task 表
    Task.objects.all().delete()

    orders = Order.objects.filter(is_done=False).order_by('order_end_date')
    order_products = sorted(
        (order_product for order in orders for order_product in order.products.filter(is_done=False)
         if has_process(order_product)),
        key=lambda p: p.order.order_end_date
    )

    # 字典缓存所有工序
    process_cache = {}
    for order in orders:
        for order_product in order.products.filter(is_done=False):
            processes = Process.objects.filter(
                product_code=order_product.product_code,
                process_i__gt=order_product.cur_process_i
            ).values('device_name', 'process_i', 'process_duration', 'process_name', 'process_capacity')

            if processes.exists():
                process_cache[order_product.id] = {
                    p['process_i']: p for p in processes
                }

    start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
    current_time = add_working_time(start_date)

    devices = Device.objects.all()

    while order_products:
        for device in devices:
            # 如果当前时间在设备的使用时间范围内，则跳过
            if device.start_time <= current_time < device.end_time:
                continue

            for order_product in order_products:

                # debug
                if order_product.product_code != "MMA-511-11001" or order_product.order.order_code != "587011":
                    order_products.remove(order_product)
                    continue
                # print(
                #     f"{order_product.order.order_code}\t{order_product.product_code}\t{device.device_name}\t{current_time}\t{order_product.end_time}")

                if current_time < order_product.end_time:
                    continue

                processes = process_cache.get(order_product.id, {})
                next_process_i = min((pi for pi in processes.keys() if pi > order_product.cur_process_i), default=None)
                process = processes.get(next_process_i)

                if process:
                    # 进行排产
                    duration = process['process_duration']

                    # 更新设备换型信息
                    raw_code = Product.objects.get(product_code=order_product.product_code).raw_code
                    is_changeover = 0
                    if not device.raw or device.raw != raw_code:
                        print(f"{device.raw}, {raw_code}")
                        duration += float(device.changeover_time)
                        is_changeover = 1
                    device.raw = raw_code

                    device.start_time = add_working_time(current_time)
                    device.end_time = add_working_time(current_time, duration)

                    # 更新产品的当前工序索引
                    order_product.cur_process_i = process['process_i']
                    order_product.end_time = device.end_time

                    # 处理 process_capacity 为空的情况
                    product_num = process.get('process_capacity')
                    if product_num is None:
                        product_num = 1  # 设置默认值

                    Task.objects.create(
                        task_start_time=device.start_time,
                        task_end_time=device.end_time,
                        order_code=order_product.order.order_code,
                        product_code=order_product.product_code,
                        process_i=process['process_i'],
                        process_name=process['process_name'],
                        device_name=device.device_name,
                        product_num=product_num,
                        is_changeover=is_changeover
                    )

                    # 移除已处理的订单产品，如果当前工序是最大序号工序
                    if is_max_process(order_product):
                        order_products.remove(order_product)
                    break
        # 更新当前时间
        current_time += timedelta(minutes=1)
