import logging

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..common.utils import log_execution
from ..models import Process

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    data = {}
    for sheet_name in xls.sheet_names[:2]:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=[1, 2])
        data[sheet_name] = df
    return data


def insert_data(df):
    for _, row in df.iterrows():
        product_code = str(row[('Unnamed: 2_level_0', '商品编号')]).strip()

        for i in range(1, 11):
            process_info = {
                'process_i': i,
                'process_name': row.get(('工序' + str(i), '工序名称'), None),
                'process_capacity': row.get(('工序' + str(i), '加工数量'), None),
                'process_duration': row.get(('工序' + str(i), '加工时间'), None),
                'device_name': row.get(('工序' + str(i), '设备名称'), None),
                'is_outside': row.get(('工序' + str(i), '是否外协'), None)
            }

            if not pd.isna(process_info['process_name']) and not pd.isna(process_info['process_duration']):
                try:
                    Process.objects.create(
                        product_code=product_code,
                        process_i=process_info['process_i'],
                        process_name=process_info['process_name'],
                        process_capacity=int(process_info['process_capacity']) if pd.notna(
                            process_info['process_capacity']) else None,
                        process_duration=float(process_info['process_duration']) if pd.notna(
                            process_info['process_duration']) else None,
                        device_name=process_info['device_name'],
                        is_outside=True if process_info['is_outside'] == "是" else False
                    )
                except (ValueError, IntegrityError, ValidationError) as e:
                    logger.error(f"Error creating process for product {product_code}: {e}")
                    continue


@log_execution
def preprocess_process(file_path='./data/产品加工用时统计进度表.xlsx'):
    data = load_data(file_path)

    for sheet_name, df in data.items():
        logger.info(f"Processing sheet: {sheet_name}")
        insert_data(df)

    logger.info("Done inserting process table")


if __name__ == "__main__":
    preprocess_process()
