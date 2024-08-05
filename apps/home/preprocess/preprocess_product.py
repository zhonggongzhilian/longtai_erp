import logging

import pandas as pd
from django.db import transaction

from ..models import Product

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def preprocess_product(file_path):
    df = pd.read_excel(file_path)

    with transaction.atomic():
        for index, row in df.iterrows():
            if pd.notna(row['净重（KG)']):
                product_code = row['商品编码'].strip()
                product_name = row['商品名称'].strip()
                product_kind = row['商品类别'].strip()
                raw_code = row['毛坯编码'].strip()
                weight = row['净重（KG)']
                if not Product.objects.filter(product_code=product_code).exists():
                    Product.objects.create(
                        product_code=product_code,
                        product_name=product_name,
                        product_kind=product_kind,
                        raw_code=raw_code,
                        weight=float(weight)
                    )
                    logger.info(f"Create {product_code} weight {weight}")
                else:
                    product = Product.objects.get(product_code=product_code.strip())
                    product.product_name = product_name
                    product.product_kind = product_kind
                    product.raw_code = raw_code
                    product.weight = weight
                    product.save()
                    logger.info(f"Update {product_code} weight {weight}")


if __name__ == "__main__":
    weight_file_path = '../data/净重.xlsx'
    preprocess_product(weight_file_path)
