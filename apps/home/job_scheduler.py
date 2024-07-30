from datetime import datetime, timedelta

from .models import Order, OrderProduct, Process, Product, Device, Tasks

# 定义工作时间范围
WORK_START_MORNING = 9
WORK_END_MORNING = 12
WORK_START_AFTERNOON = 13
WORK_END_AFTERNOON = 18


def is_working_time(current_time):
    """
    判断当前时间是否在工作时间内
    """
    current_hour = current_time.hour
    return (WORK_START_MORNING <= current_hour < WORK_END_MORNING) or (
            WORK_START_AFTERNOON <= current_hour < WORK_END_AFTERNOON)


def get_next_working_time(start_time, duration_minutes):
    """
    根据工作时间计算预计完成时间
    """
    current_time = start_time
    remaining_minutes = duration_minutes

    while remaining_minutes > 0:
        if is_working_time(current_time):
            end_of_work_period = datetime(current_time.year, current_time.month, current_time.day,
                                          WORK_END_MORNING if current_time.hour < WORK_START_AFTERNOON else WORK_END_AFTERNOON,
                                          0)
            if end_of_work_period < current_time:
                end_of_work_period = datetime(current_time.year, current_time.month, current_time.day,
                                              WORK_END_AFTERNOON, 0)

            work_period_minutes = (end_of_work_period - current_time).seconds // 60
            if work_period_minutes > remaining_minutes:
                current_time += timedelta(minutes=remaining_minutes)
                remaining_minutes = 0
            else:
                remaining_minutes -= work_period_minutes
                current_time = datetime(current_time.year, current_time.month, current_time.day,
                                        WORK_START_AFTERNOON, 0) if current_time.hour < WORK_START_AFTERNOON else \
                    datetime(current_time.year, current_time.month, current_time.day + 1,
                             WORK_START_MORNING, 0)
        else:
            current_time += timedelta(minutes=1)

    return current_time


def get_orders_sorted_by_delivery_date():
    """
    获取按交付时间排序的订单
    """
    orders = Order.objects.all().order_by('delivery_date')
    return orders


def get_order_products(order):
    """
    获取订单中所有需要生产的产品及其数量
    """
    products = OrderProduct.objects.filter(order=order)
    return products


def get_processes_for_product(product_code):
    """
    获取指定产品的工序
    """
    processes = Process.objects.filter(product_code__product_code=product_code).order_by('process_sequence', 'duration')
    return processes


def update_device_raw(device_name, new_raw_code):
    """
    更新设备的毛坯信息
    """
    device = Device.objects.filter(device_name=device_name).first()
    if device:
        device.raw = new_raw_code
        device.save()


def schedule_production():
    """
    排产逻辑
    """
    orders = get_orders_sorted_by_delivery_date()

    results = []  # 用于存储排产结果

    # 设置开始时间
    start_time = datetime(2023, 5, 1, WORK_START_MORNING, 0)
    print(f"{start_time=}")

    for order in orders:
        order_products = get_order_products(order)

        for product in order_products:
            product_code = product.product_code
            try:
                product_raw_code = Product.objects.filter(product_code=product_code).first().raw.raw_code
            except AttributeError as e:
                product_raw_code = "TG-VH-2-50-C"
            processes = get_processes_for_product(product_code)

            current_time = start_time

            for process in processes:
                process_duration = process.duration
                equipment = process.equipment
                process_sequence = process.process_sequence

                # 获取设备当前的毛坯
                device = Device.objects.filter(device_name=equipment).first()
                device_raw_code = device.raw if device else None

                # 判断是否需要换型
                changeover = False
                if device_raw_code and device_raw_code != product_raw_code:
                    changeover = True
                    # 假设换型时间为10分钟
                    process_duration += 10

                # 计算预计完成时间
                completion_time = get_next_working_time(current_time, process_duration)

                # 输出操作信息
                results.append({
                    'execution_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'completion_time': completion_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'changeover': 'Yes' if changeover else 'No',
                    'order': order.order_id,
                    'product': product_code,
                    'process_sequence': process_sequence,
                    'process_name': process.process_name,
                    'device': equipment
                })

                # 更新设备的毛坯信息
                if device:
                    update_device_raw(equipment, product_raw_code)

                # 更新当前时间为完成时间
                current_time = completion_time

    # 打印排产结果
    for result in results:
        print(f"Process Sequence: {result['process_sequence']}")
        print(f"Execution Time: {result['execution_time']}")
        print(f"Expected Completion Time: {result['completion_time']}")
        print(f"Changeover: {result['changeover']}")
        print(f"Order ID: {result['order']}")
        print(f"Product Code: {result['product']}")
        print(f"Process Name: {result['process_name']}")
        print(f"Device: {result['device']}")
        print("-----")

    save_production_results(results)


def save_production_results(results):
    """
    保存生产结果到数据库
    """
    for result in results:
        Tasks.objects.create(
            execution_time=result['execution_time'],
            completion_time=result['completion_time'],
            changeover=result['changeover'],
            order=result['order'],
            product=result['product'],
            process_sequence=result['process_sequence'],
            process_name=result['process_name'],
            device=result['device']
        )


if __name__ == "__main__":
    schedule_production()
