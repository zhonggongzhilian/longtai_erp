from datetime import datetime, timedelta, time

from django.utils import timezone

from .models import Device, Order, Process, Task, Product


def calculate_workday_ratio(current_time):
    # 定义工作时间段
    work_start_morning = time(9, 0)
    work_end_morning = time(12, 0)
    work_start_afternoon = time(13, 0)
    work_end_afternoon = time(18, 0)

    # 获取当前日期的日期部分
    today_date = current_time.date()

    # 计算工作时间段的开始和结束时间（时区感知）
    work_start_morning_datetime = timezone.make_aware(datetime.combine(today_date, work_start_morning))
    work_end_morning_datetime = timezone.make_aware(datetime.combine(today_date, work_end_morning))
    work_start_afternoon_datetime = timezone.make_aware(datetime.combine(today_date, work_start_afternoon))
    work_end_afternoon_datetime = timezone.make_aware(datetime.combine(today_date, work_end_afternoon))

    # 计算一天的工作时间总长度（以分钟为单位）
    total_work_minutes = (
            (work_end_morning_datetime - work_start_morning_datetime).seconds / 60 +
            (work_end_afternoon_datetime - work_start_afternoon_datetime).seconds / 60
    )

    # 计算当前时间在工作时间段内的时间（以分钟为单位）
    current_time_minutes = 0
    if work_start_morning_datetime <= current_time <= work_end_morning_datetime:
        current_time_minutes = (current_time - work_start_morning_datetime).seconds / 60
    elif work_start_afternoon_datetime <= current_time <= work_end_afternoon_datetime:
        current_time_minutes = (
                (work_end_morning_datetime - work_start_morning_datetime).seconds / 60 +
                (current_time - work_start_afternoon_datetime).seconds / 60
        )

    # 计算当前时间在一天工作时间中的比例
    workday_ratio = (current_time_minutes / total_work_minutes) * 100

    return workday_ratio


def update_progress(progress):
    """
    用于更新进度的辅助函数。
    """
    with open('./progress.txt', 'w') as f:
        f.write(str(progress))


def is_max_process(order_product, process_cache):
    """
    判断当前工序是否是订单产品的最大工序。
    """
    processes = process_cache.get(order_product.id, {})
    next_process_i = min((pi for pi in processes.keys() if pi > order_product.cur_process_i), default=None)
    process = processes.get(next_process_i)
    if not process:
        return 1
    return 0


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
        work_start_morning = end_time.replace(hour=7, minute=30, second=0, microsecond=0)
        work_end_morning = end_time.replace(hour=11, minute=30, second=0, microsecond=0)
        work_start_afternoon = end_time.replace(hour=12, minute=0, second=0, microsecond=0)
        work_end_afternoon = end_time.replace(hour=17, minute=0, second=0, microsecond=0)
        work_start_night = end_time.replace(hour=17, minute=0, second=0, microsecond=0)
        work_end_night = end_time.replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1)

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
                end_time = work_start_night
        elif end_time < work_start_night:
            end_time = work_start_night
        elif end_time < work_end_night:
            available_time = (work_end_night - end_time).seconds / 60
            if duration <= available_time:
                end_time += timedelta(minutes=duration)
                duration = -1
            else:
                duration -= available_time
                end_time = work_start_morning + timedelta(days=1)
        else:
            # 处理结束时间在夜班工作结束后的情况
            end_time = work_start_morning + timedelta(days=1)

    return end_time


def add_task(device, current_time, order_product, ):
    pass


def test_debug(order_product, order_products, debug=0):
    if debug == 0:
        return 0
    if order_product.product_code != "TG-VH1-10I" or order_product.order.order_code != "I054239-C":
        order_products.remove(order_product)
        return 1
    return 0


def schedule_production(start_date_str='2024-01-10', fast=False):
    start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
    current_time = add_working_time(start_date)

    # 清空 Task 表
    Task.objects.all().delete()

    orders = Order.objects.filter(is_done=False,
                                  order_start_date__lte=start_date.strftime('%Y-%m-%d')
                                  ).order_by('order_end_date')
    order_products = sorted(
        (order_product for order in orders for order_product in order.products.filter(is_done=False)
         if has_process(order_product)),
        key=lambda p: p.order.order_end_date
    )

    # remove_order_products_with_outside_process(order_products)

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

    devices = Device.objects.all()

    sc_start = datetime.now()
    count = 0
    while order_products:
        if fast:
            if current_time.date() != start_date.date():
                break

        for device in devices:
            dv_start = datetime.now()
            # 如果当前时间在设备的使用时间范围内，则跳过
            if device.start_time <= current_time <= device.end_time:
                continue

            device_current_time = max(device.start_time, current_time)

            has_no_changeover = False
            for order_product in order_products:
                # debug
                if test_debug(order_product, order_products):
                    continue

                # 如果当前产品的上一个工序还没完成，则跳过
                if current_time < order_product.end_time:
                    continue

                try:
                    raw_code = Product.objects.get(product_code=order_product.product_code).raw_code
                except Exception as e:
                    raw_code = "Null"

                if device.raw == raw_code:
                    processes = process_cache.get(order_product.id, {})
                    next_process_i = min((pi for pi in processes.keys() if pi >= order_product.cur_process_i),
                                         default=None)
                    process = processes.get(next_process_i)

                    if process:
                        if device.device_name not in process['device_name'].split('/'):
                            continue
                        process_capacity = process['process_capacity']
                        if not process_capacity:
                            process_capacity = 1
                        # 进行排产
                        duration = process['process_duration']

                        device.start_time = add_working_time(device_current_time)
                        device.end_time = add_working_time(device_current_time, duration)

                        Task.objects.create(
                            task_start_time=device.start_time,
                            task_end_time=device.end_time,
                            order_code=order_product.order.order_code,
                            product_code=order_product.product_code,
                            process_i=process['process_i'],
                            process_name=process['process_name'],
                            device_name=device.device_name,
                            product_num=process_capacity,
                            is_changeover=0
                        )
                        # 移除已处理的订单产品，如果当前工序是最大序号工序
                        device_current_time = device.end_time
                        order_product.product_num_done += process_capacity

                        count = 0

                        # 更新产品的当前工序索引
                        if order_product.product_num_todo <= order_product.product_num_done:

                            order_product.end_time = device.end_time
                            order_product.product_num_done = 0

                            if is_max_process(order_product, process_cache):
                                order_products.remove(order_product)

                            order_product.cur_process_i = process['process_i'] + 1
                        else:
                            order_product.cur_process_i = process['process_i']

                        has_no_changeover = True
                        break

            if has_no_changeover:
                continue

            for order_product in order_products:

                # debug
                if test_debug(order_product, order_products):
                    continue

                if current_time < order_product.end_time:
                    continue

                processes = process_cache.get(order_product.id, {})
                next_process_i = min((pi for pi in processes.keys() if pi >= order_product.cur_process_i), default=None)
                process = processes.get(next_process_i)

                if process:

                    if device.device_name not in process['device_name'].split('/'):
                        continue
                    process_capacity = process['process_capacity']
                    if not process_capacity:
                        process_capacity = 1

                    duration = process['process_duration']

                    # 更新设备换型信息
                    try:
                        raw_code = Product.objects.get(product_code=order_product.product_code).raw_code
                    except Exception as e:
                        raw_code = "Null"

                    is_changeover = 0
                    if device.raw != raw_code:
                        is_changeover = 1
                    device.raw = raw_code if raw_code != "Null" else None

                    if is_changeover:
                        duration += float(device.changeover_time)

                    device.start_time = add_working_time(device_current_time)
                    device.end_time = add_working_time(device_current_time, duration)

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
                    count = 0

                    # 移除已处理的订单产品，如果当前工序是最大序号工序
                    order_product.product_num_done += process_capacity
                    if order_product.product_num_todo <= order_product.product_num_done:

                        order_product.end_time = device.end_time
                        order_product.product_num_done = 0

                        if is_max_process(order_product, process_cache):
                            order_products.remove(order_product)

                        order_product.cur_process_i = process['process_i'] + 1
                    else:
                        order_product.cur_process_i = process['process_i']
                    break
            dv_end = datetime.now()
        # 获取所有 order_products 中最早的 end_time
        current_time = get_current_time(order_products, devices, current_time, start_date)
        progress = calculate_workday_ratio(current_time)
        update_progress(progress)
        count += 1

    sc_end = datetime.now()


def get_current_time(order_products, devices, current_time, start_date):
    earliest_op_end_time = min((op.end_time for op in order_products), default=start_date)
    earliest_dv_end_time = min((dv.end_time for dv in devices), default=start_date)
    return add_working_time(max(earliest_op_end_time, earliest_dv_end_time, current_time) + timedelta(minutes=1))
