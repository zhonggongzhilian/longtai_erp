import logging
import sqlite3
from collections import defaultdict
import pandas as pd
from ..common.utils import log_execution

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
        import os
        df.to_csv(os.path.join('./data/' + sheet_name + '.csv'))
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


def create_tables(conn):
    cursor = conn.cursor()
    # 创建表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS process_flows (
        flow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT,
        FOREIGN KEY (product_code) REFERENCES products (product_code)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processes (
        process_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id INTEGER,
        process_name TEXT,
        quantity INTEGER,
        duration REAL,
        equipment TEXT,
        completion_date TEXT,
        flow_range INTEGER,
        FOREIGN KEY (flow_id) REFERENCES process_flows (flow_id)
    )
    ''')
    conn.commit()


def insert_data(conn, product_processes):
    cursor = conn.cursor()

    for product, flows in product_processes.items():
        cursor.execute('INSERT OR IGNORE INTO products (product_code) VALUES (?)', (product,))
        product_id = cursor.lastrowid

        for flow in flows:
            cursor.execute('INSERT INTO process_flows (product_code) VALUES (?)', (product,))
            flow_id = cursor.lastrowid

            for process in flow:
                cursor.execute('''
                INSERT INTO processes (flow_id, process_name, quantity, duration, equipment, completion_date, flow_range)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    flow_id,
                    process['工序名称'],
                    process['加工数量'],
                    process['加工时间'],
                    process['设备名称'],
                    process['统计完成时间'],
                    process['flow_range']
                ))
    conn.commit()


@log_execution
def preprocess_process(file_path='./data/产品加工用时统计进度表.xlsx', db_path='./database/longtai.db'):
    data = load_data(file_path)
    conn = sqlite3.connect(db_path)
    create_tables(conn)

    for sheet_name, df in data.items():
        logger.info(f"Processing sheet: {sheet_name}")
        product_processes = process_data(df)
        insert_data(conn, product_processes.to_dict())

    conn.close()
    logger.info("Done insert process table")


if __name__ == "__main__":
    preprocess_process()