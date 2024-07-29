import logging
import pandas as pd
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..common.utils import log_execution
from ..models import Product, Process

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_data(file_path):
    # 读取 Excel 文件
    xls = pd.ExcelFile(file_path)
    data = {}
    for sheet_name in xls.sheet_names[:2]:
        # 读取每个 sheet，并设置正确的 header 行
        df = pd.read_excel(xls, sheet_name=sheet_name, header=[1, 2])
        data[sheet_name] = df
    return data


def insert_data(df):
    for _, row in df.iterrows():
        product_code = str(row[('产品型号', 'Unnamed: 1_level_1')]).strip()
        try:
            product, created = Product.objects.get_or_create(product_code=product_code)
        except IntegrityError as e:
            logger.error(f"Error creating product {product_code}: {e}")
            continue

        for i in range(1, 11):  # 工序 1 到 工序 10
            process_info = {
                'process_sequence': i,  # 工序顺序
                'process_name': row.get(('工序' + str(i), '工序名称'), None),
                'quantity': row.get(('工序' + str(i), '加工数量'), None),
                'duration': row.get(('工序' + str(i), '加工时间'), None),
                'equipment': row.get(('工序' + str(i), '设备名称'), None),
                'completion_date': row.get(('工序' + str(i), '统计完成时间（日期）'), None)
            }

            # 只插入 process_name 非空的记录
            if not pd.isna(process_info['process_name']) and not pd.isna(process_info['duration']):
                try:
                    Process.objects.create(
                        product_code=product,
                        process_sequence=process_info['process_sequence'],
                        process_name=process_info['process_name'],
                        quantity=int(process_info['quantity']) if pd.notna(process_info['quantity']) else None,
                        duration=float(process_info['duration']) if pd.notna(process_info['duration']) else None,
                        equipment=process_info['equipment'],
                        completion_date=process_info['completion_date']
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