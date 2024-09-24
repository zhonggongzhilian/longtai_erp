import logging

import pandas as pd
from django.db import transaction, IntegrityError

from ..common.utils import log_execution
from ..models import Raw

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def insert_raw(raw_code, raw_name, raw_date_add, raw_num):
    with transaction.atomic():
        # 尝试查找是否存在相同 raw_name 和 raw_date_add 的记录
        raw, created = Raw.objects.get_or_create(
            raw_code=raw_code,
            defaults={
                'raw_num': raw_num,
                'raw_name': raw_name,
                'raw_date_add': raw_date_add,
            }
        )
        if not created:
            # 如果记录已经存在，更新字段值
            raw.raw_num += raw_num  # 增加数量
            raw.raw_date_add = raw_date_add
            raw.save()


def process_file(file_path):
    df = pd.read_excel(file_path, header=3).ffill()

    for index, row in df.iterrows():
        if row['商品编号'].strip() != '合计':
            insert_raw(row['商品编号'], row['商品名称'], row['单据日期'], row['数量'])


@log_execution
def preprocess_raw(file_path=f"../upload_data/毛坯表.xlsx"):
    with transaction.atomic():
        process_file(file_path)
    logger.info("Done processing raw and product data")


if __name__ == "__main__":
    process_file(f"/Users/shining/Documents/GitHub/longtai_erp/apps/home/upload_data/毛坯表.xls")
