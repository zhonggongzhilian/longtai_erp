import logging

import pandas as pd

from ..models import Order, OrderProduct

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def insert_order(order):
    Order.objects.update_or_create(
        order_id=order.order_id,
        defaults={
            'order_date': order.order_date,
            'associate_sale_id': order.associate_sale_id,
            'business_kind': order.business_kind,
            'associate_purchase_order_id': order.associate_purchase_order_id,
            'saler': order.saler,
            'customer': order.customer,
            'sale_amount': order.sale_amount,
            'discount_price': order.discount_price,
            'discounted_price': order.discounted_price,
            'order_state': order.order_state,
            'delivery_date': order.delivery_date,
            'order_maker': order.order_maker,
            'order_making_time': order.order_making_time,
            'reviewer': order.reviewer,
            'remark': order.remark,
            'delivery_method': order.delivery_method,
            'print_count': order.print_count,
        }
    )


def insert_product(product, order_id):
    OrderProduct.objects.update_or_create(
        order_id=order_id,
        product_code=product.product_code,
        defaults={
            'product_name': product.product_name,
            'product_model': product.product_model,
            'attribute': product.attribute,
            'barcode': product.barcode,
            'category': product.category,
            'product_remark': product.product_remark,
            'unit': product.unit,
            'quantity': product.quantity,
            'sale_price': product.sale_price,
            'estimated_purchase_price': product.estimated_purchase_price,
            'discount_rate': product.discount_rate,
            'discount_amount': product.discount_amount,
            'discount': product.discount,
            'discounted_price': product.discounted_price,
            'amount': product.amount,
            'reference_cost': product.reference_cost,
            'estimated_gross_profit': product.estimated_gross_profit,
            'estimated_gross_profit_rate': product.estimated_gross_profit_rate,
            'latest_purchase_price': product.latest_purchase_price,
            'product_house': product.product_house,
            'remark': product.remark,
            'available_stock': product.available_stock,
            'basic_unit': product.basic_unit,
            'basic_unit_quantity': product.basic_unit_quantity,
            'whole_scatter': product.whole_scatter,
            'conversion_formula': product.conversion_formula,
            'is_gift': product.is_gift,
            'shelf': product.shelf,
            'undelivered_quantity': product.undelivered_quantity,
            'undelivered_basic_quantity': product.undelivered_basic_quantity,
            'delivered_quantity': product.delivered_quantity,
            'delivered_basic_quantity': product.delivered_basic_quantity,
            'row_status': product.row_status,
            'custom_column_one': product.custom_column_one,
            'custom_column_two': product.custom_column_two,
            'custom_column_three': product.custom_column_three,
            'custom_column_four': product.custom_column_four,
            'custom_column_five': product.custom_column_five,
        }
    )


def preprocess_order(file_path='./data/销货订单导出_202306241022.xlsx'):
    df = pd.read_excel(file_path, header=4).ffill()

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
