import logging
from collections import defaultdict

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..common.utils import log_execution
from ..models import Product, ProcessFlow, Process

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ProductProcess:
    def __init__(self):
        self.data = defaultdict(list)

    def add_process_flow(self, product, process_flow):
        self.data[product.strip()].append(process_flow)  # 修剪产品编码

    def to_dict(self):
        return dict(self.data)


def load_data(file_path):
    # 读取 Excel 文件
    xls = pd.ExcelFile(file_path)
    data = {}
    for sheet_name in xls.sheet_names[:2]:
        # 读取每个 sheet，并设置正确的 header 行
        df = pd.read_excel(xls, sheet_name=sheet_name, header=[1, 2])
        # 填充整个 DataFrame 的缺失值，用前一行数据进行填充
        df = df.ffill()
        data[sheet_name] = df
    return data


def process_data(df):
    # 初始化产品数据结构
    product_processes = ProductProcess()

    # 遍历数据框，收集每个产品型号的工序信息
    for _, row in df.iterrows():
        product = str(row[('产品型号', 'Unnamed: 1_level_1')]).strip()  # 修剪产品编码
        process_flow = []
        for i in range(1, 11):  # 工序 1 到 工序 10
            process_info = {
                '工序名称': row.get(('工序' + str(i), '工序名称'), None),
                '加工数量': row.get(('工序' + str(i), '加工数量'), None),
                '加工时间': row.get(('工序' + str(i), '加工时间'), None),
                '设备名称': row.get(('工序' + str(i), '设备名称'), None),
                '统计完成时间': row.get(('工序' + str(i), '统计完成时间（日期）'), None),
                'flow_range': i
            }
            if pd.notna(process_info['工序名称']):  # 只有当工序名称不为空时才添加
                process_flow.append(process_info)
        if process_flow:
            product_processes.add_process_flow(product, process_flow)

    return product_processes


def insert_data(product_processes):
    for product_code, flows in product_processes.items():
        try:
            product, created = Product.objects.get_or_create(product_code=product_code)
        except IntegrityError as e:
            logger.error(f"Error creating product {product_code}: {e}")
            continue

        for flow in flows:
            try:
                process_flow = ProcessFlow.objects.create(product=product)
            except IntegrityError as e:
                logger.error(f"Error creating process flow for product {product_code}: {e}")
                continue

            for process in flow:
                try:
                    Process.objects.create(
                        flow=process_flow,
                        process_name=process['工序名称'],
                        quantity=int(process['加工数量']) if pd.notna(process['加工数量']) else None,
                        duration=float(process['加工时间']) if pd.notna(process['加工时间']) else None,
                        equipment=process['设备名称'],
                        completion_date=process['统计完成时间'],
                        flow_range=process['flow_range']
                    )
                except (ValueError, IntegrityError, ValidationError) as e:
                    logger.error(f"Error creating process for product {product_code}: {e}")
                    continue


@log_execution
def preprocess_process(file_path='./data/产品加工用时统计进度表.xlsx'):
    data = load_data(file_path)

    for sheet_name, df in data.items():
        logger.info(f"Processing sheet: {sheet_name}")
        product_processes = process_data(df)
        insert_data(product_processes.to_dict())

    logger.info("Done insert process table")


if __name__ == "__main__":
    preprocess_process()
