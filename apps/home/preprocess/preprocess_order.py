import logging

import pandas as pd

from ..models import Order, OrderProduct

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def insert_order(order):
    Order.objects.update_or_create(
        order_code=order.order_code,
        defaults={
            'order_date': order.order_start_date,
            'delivery_date': order.order_end_date,
        }
    )


def insert_product(product, order_code):
    OrderProduct.objects.update_or_create(
        order_code=order_code,
        product_code=product.product_code,
        defaults={
            'product_name': product.product_name,
            'product_kind': product.product_kind,
            'product_num_todo': product.product_num_todo,
        }
    )


def preprocess_order(file_path='./data/销货订单导出_202306241022.xlsx'):
    df = pd.read_excel(file_path, header=4).ffill()
    df = df[~df['商品编码'].str.contains('合计', na=False)]

    orders = []
    for order_id, group in df.groupby('订单编号'):
        order_row = group.iloc[0]
        products_rows = group
        order, products = Order.from_dataframe_rows(order_row, products_rows)
        orders.append((order, products))

    for order, products in orders:
        order.save()
        for product in products:
            product.save()


if __name__ == "__main__":
    preprocess_order()
