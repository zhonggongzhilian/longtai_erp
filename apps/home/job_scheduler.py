from datetime import datetime, timedelta
from django.utils import timezone
from .models import Device, Order, Process


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


def schedule_production(start_date_str='2024-01-01'):
    devices = Device.objects.all()
    orders = Order.objects.filter(is_done=False).order_by('order_end_date')
    order_products = sorted(
        (order_product for order in orders for order_product in order.products.filter(is_done=False)
         if has_process(order_product)),
        key=lambda p: p.order.order_end_date
    )

    # 使用一个字典缓存所有工序，避免重复查询
    process_cache = {}
    for order in orders:
        for order_product in order.products.filter(is_done=False):
            processes = Process.objects.filter(
                product_code=order_product.product_code,
                process_i__gt=order_product.cur_process_i
            ).values('device_name', 'process_i', 'process_duration')

            if processes.exists():
                process_cache[order_product.id] = {
                    p['process_i']: p for p in processes
                }

    start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
    current_time = start_date

    while order_products:
        for device in devices:
            # 如果当前时间在设备的使用时间范围内，则跳过
            if device.start_time <= current_time < device.end_time:
                continue
            # print(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} {device.device_name} is free.")

            for order_product in order_products:
                next_process_i = order_product.cur_process_i + 1
                processes = process_cache.get(order_product.id, {})
                process = processes.get(next_process_i)

                if process:
                    # 进行排产
                    duration = process['process_duration']
                    device.start_time = current_time
                    device.end_time = current_time + timedelta(minutes=duration)

                    # 更新产品的当前工序索引
                    order_product.cur_process_i = process['process_i']

                    print(f"Schedule: "
                          f"remain: {len(order_products)}\t"
                          f"product: {order_product.product_code}\t"
                          f"device: {device.device_name}\t"
                          f"process i: {process['process_i']}\t"
                          f"start: {device.start_time.strftime('%Y-%m-%d %H:%M:%S')}\t"
                          f"end: {device.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

                    # 移除已处理的订单产品，如果当前工序是最大序号工序
                    if is_max_process(order_product):
                        order_products.remove(order_product)
                        print(f"\tFinish {order_product.order.order_code} {order_product.product_code}")

                    break

        # 更新当前时间
        current_time += timedelta(minutes=1)


# 调用函数
schedule_production('2024-01-01')