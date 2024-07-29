from django.utils.dateparse import parse_date
from .models import Order


def get_earliest_delivery_order():
    """
    获取最早需要交付的订单
    """
    # 获取所有订单，并按交货日期升序排列
    orders = Order.objects.all().order_by('delivery_date')

    # 如果有订单，返回最早的一个
    if orders.exists():
        return orders.first()
    return None