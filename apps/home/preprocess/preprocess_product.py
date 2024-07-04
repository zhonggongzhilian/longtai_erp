import logging
import pandas as pd
from django.db import IntegrityError, transaction
from ..models import Product

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def insert_or_update_product(product_code, weight):
    try:
        product, created = Product.objects.get_or_create(product_code=product_code)
        product.weight = weight
        product.save()
        if created:
            logger.info(f"Inserted product {product_code} with weight {weight}")
        else:
            logger.info(f"Updated product {product_code} with weight {weight}")
    except IntegrityError as e:
        logger.error(f"Error inserting/updating product {product_code}: {e}")


def update_product_weights(weights):
    # 插入或更新产品重量
    for product_code, weight in weights.items():
        insert_or_update_product(product_code, weight)


def load_weight_data(file_path):
    # 读取 Excel 文件
    df = pd.read_excel(file_path)

    # 转换为字典
    weights = dict(zip(df['PartNumber零件号码'], df['Weight重量(kg)']))
    return weights


def preprocess_product(file_path):
    # 加载重量数据
    weights = load_weight_data(file_path)

    # 更新产品重量
    with transaction.atomic():
        update_product_weights(weights)

    logger.info("Done updating product weights")


if __name__ == "__main__":
    weight_file_path = '../data/净重.xlsx'
    preprocess_product(weight_file_path)