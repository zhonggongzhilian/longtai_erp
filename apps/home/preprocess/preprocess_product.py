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
            if pd.notna(row['Weight重量(kg)']):
                product_code = row['PartNumber零件号码']
                weight = row['Weight重量(kg)']
                if not Product.objects.filter(product_code=product_code).exists():
                    Product.objects.create(
                        product_code=product_code.strip(),
                        weight=float(weight)
                    )
                    logger.info(f"Create {product_code} weight {weight}")
                else:
                    product = Product.objects.get(product_code=product_code.strip())
                    product.weight = weight
                    product.save()
                    logger.info(f"Update {product_code} weight {weight}")


if __name__ == "__main__":
    weight_file_path = '../data/净重.xlsx'
    preprocess_product(weight_file_path)
