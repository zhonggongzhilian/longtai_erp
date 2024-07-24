# processing.py

import logging
from datetime import datetime, timedelta, time
from django.db import transaction
from .models import Order, OrderProduct, Process, ExchangeTypeTime, Product, OrderProcessingResult

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('process_log.log')
formatter = logging.Formatter('%(asctime)s | %(filename)s | %(name)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_orders_sorted_by_delivery_date():
    orders = Order.objects.all().order_by('delivery_date')
    if not orders:
        raise ValueError("No orders found.")
    return orders


def get_order_products(order_id):
    products = OrderProduct.objects.filter(order__order_id=order_id)
    if not products:
        raise ValueError(f"No products found for order id: {order_id}")
    return products


def get_process_flow(product_code):
    process_flow = Process.objects.filter(product__product_code=product_code.strip()).first()
    if not process_flow:
        raise ValueError(f"No process flow found for product code: {product_code}")
    return process_flow


def get_processes(flow_id):
    processes = Process.objects.filter(flow_id=flow_id)
    if not processes:
        raise ValueError(f"No processes found for flow id: {flow_id}")
    return processes


def get_exchange_time(equipment):
    exchange_time = ExchangeTypeTime.objects.filter(device_name=equipment).first()
    return int(exchange_time.exchange_time) if exchange_time else 0


def adjust_for_working_hours(start_time, duration):
    """
    Adjust the given start_time and duration to fit within working hours (9 AM - 12 PM and 2 PM - 6 PM).
    """
    work_start = time(9, 0)
    work_end = time(18, 0)
    lunch_start = time(12, 0)
    lunch_end = time(14, 0)

    end_time = start_time  # 初始化 end_time

    while duration > 0:
        if work_start <= start_time.time() < lunch_start:
            available_time = (datetime.combine(start_time.date(), lunch_start) - start_time).seconds // 60
            if duration <= available_time:
                end_time = start_time + timedelta(minutes=duration)
                duration = 0
            else:
                start_time = start_time + timedelta(minutes=available_time) + timedelta(hours=2)
                duration -= available_time
        elif lunch_end <= start_time.time() < work_end:
            available_time = (datetime.combine(start_time.date(), work_end) - start_time).seconds // 60
            if duration <= available_time:
                end_time = start_time + timedelta(minutes=duration)
                duration = 0
            else:
                start_time = start_time + timedelta(minutes=available_time) + timedelta(hours=15)
                duration -= available_time
        else:
            start_time += timedelta(days=1)
            start_time = start_time.replace(hour=9, minute=0, second=0)

    return start_time, end_time


@transaction.atomic
def process_orders(start_date=None):
    orders = get_orders_sorted_by_delivery_date()

    equipment_usage = {}
    all_orders_schedule = []
    order_details = []
    order_start_end_times = []

    # 如果未指定开始日期，使用默认值 2023-01-01
    if start_date is None:
        start_date = datetime(2023, 1, 1, 9, 0)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=9, minute=0, second=0, microsecond=0)

    current_time = start_date

    for order in orders:
        order_id = order.order_id
        delivery_date = order.delivery_date
        products = get_order_products(order_id)
        product_codes = [product.product_code for product in products]

        order_schedule = []
        order_start_time = current_time
        total_weight = 0  # 累加每个订单的已生产产品重量

        for product_code in product_codes:
            try:
                process_flow = get_process_flow(product_code)
                processes = get_processes(process_flow.id)
            except ValueError as e:
                logger.warning(str(e))
                print(str(e))
                continue

            product_start_time = current_time

            for process in processes:
                process_id = process.id
                flow_id = process.flow_id
                process_name = process.process_name
                quantity = process.quantity
                duration = process.duration
                equipment = process.equipment
                completion_date = process.completion_date
                flow_range = process.flow_range

                if equipment in equipment_usage:
                    current_product_code = equipment_usage[equipment]
                    if current_product_code != product_code:
                        exchange_time = get_exchange_time(equipment)
                        start_exchange_time = current_time
                        current_time += timedelta(minutes=exchange_time)
                        current_time, _ = adjust_for_working_hours(current_time, 0)
                        end_exchange_time = current_time
                        order_details.append((order_id, product_code, process_name, equipment, start_exchange_time, end_exchange_time, "换型"))

                equipment_usage[equipment] = product_code

                start_time, end_time = adjust_for_working_hours(current_time, duration)
                order_schedule.append((product_code, process_name, equipment, start_time, end_time))
                order_details.append((order_id, product_code, process_name, equipment, start_time, end_time, "加工"))
                current_time = end_time

            product_end_time = current_time
            all_orders_schedule.append((order_id, product_code, product_start_time, product_end_time))

            # 累加产品重量
            product = Product.objects.get(product_code=product_code)
            total_weight += product.weight

        if not order_schedule:
            continue
        order_end_time = max(end_time for _, _, _, _, end_time in order_schedule)
        order_start_end_times.append((order_id, order_start_time, order_end_time))

        if order_end_time > datetime.strptime(delivery_date, '%Y-%m-%d'):
            logger.warning(f"Order {order_id} cannot be delivered on time.")
            print(f"Order {order_id} cannot be delivered on time.")
            return
        else:
            logger.info(f"Order {order_id} can be delivered on time.")

        # 保存结果到 OrderProcessingResult 表
        for detail in order_details:
            OrderProcessingResult.objects.create(
                time=detail[4],
                operation=detail[6],
                order=Order.objects.get(order_id=detail[0]),
                delivery_date=order.delivery_date,
                product=Product.objects.get(product_code=detail[1]),
                equipment=detail[3],
                produced_weight=total_weight
            )

    # 按订单输出生产时间顺序表
    for order_id, start_time, end_time in order_start_end_times:
        print(f"Order {order_id} from {start_time} to {end_time}".replace('\n', ' '))
        order_product_schedules = [sched for sched in all_orders_schedule if sched[0] == order_id]
        for sched in order_product_schedules:
            print(f"  Product {sched[1]} from {sched[2]} to {sched[3]}".replace('\n', ' '))
            process_schedules = [detail for detail in order_details if detail[0] == order_id and detail[1] == sched[1]]
            for detail in process_schedules:
                print(f"    Process {detail[2]} on {detail[3]} from {detail[4]} to {detail[5]} ({detail[6]})".replace('\n', ' '))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process orders.")
    parser.add_argument("--start_date", type=str, default="2023-01-01", help="Start date for processing in YYYY-MM-DD format.")

    args = parser.parse_args()
    process_orders(args.start_date)