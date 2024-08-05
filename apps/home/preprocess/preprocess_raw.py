import logging

import pandas as pd
from django.db import transaction, IntegrityError

from ..common.utils import log_execution
from ..models import Raw

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def insert_raw(raw_code, raw_name):
    try:
        raw, created = Raw.objects.get_or_create(raw_code=raw_code, defaults={'raw_name': raw_name})
        if not created and raw.raw_name != raw_name:
            raw.raw_name = raw_name
            raw.save()
        return raw.raw_code
    except IntegrityError as e:
        logger.error(f"Error inserting/updating raw {raw_code}: {e}")
        return None


def process_file(file_path):
    df = pd.read_excel(file_path, header=1)

    for index, row in df.iterrows():
        if pd.notna(row['毛坯料号']) and pd.notna(row['中文名称']):
            insert_raw(row['毛坯料号'], row['中文名称'])


@log_execution
def preprocess_raw(file_path=f"./data/毛坯和成品对应表.xlsx"):
    with transaction.atomic():
        process_file(file_path)
    logger.info("Done processing raw and product data")


if __name__ == "__main__":
    preprocess_raw()
