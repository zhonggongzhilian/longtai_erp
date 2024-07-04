import logging
import sqlite3

import pandas as pd

from ..common.utils import log_execution

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Raw:
    def __init__(self, raw_code, raw_name):
        self.raw_code = raw_code
        self.raw_name = raw_name


class Product:
    def __init__(self, product_code, product_category, raw_code):
        self.product_code = product_code
        self.product_category = product_category
        self.raw_code = raw_code


class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw (
            raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_code TEXT UNIQUE,
            raw_name TEXT
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE,
            product_category TEXT,
            raw_code TEXT,
            FOREIGN KEY(raw_code) REFERENCES raw(raw_code)
        )
        ''')

        self.conn.commit()

    def insert_raw(self, raw):
        if raw.raw_code and raw.raw_name:  # 检查是否为空
            self.cursor.execute('''
            INSERT OR IGNORE INTO raw(raw_code, raw_name) VALUES (?, ?)
            ''', (raw.raw_code, raw.raw_name))
            self.conn.commit()
            self.cursor.execute('SELECT raw_id FROM raw WHERE raw_code = ?', (raw.raw_code,))
            return raw.raw_code
        return None

    def insert_product(self, product):
        if product.product_code and product.raw_code:  # 检查是否为空
            self.cursor.execute('''
            INSERT OR IGNORE INTO products (product_code, product_category, raw_code) VALUES (?, ?, ?)
            ''', (product.product_code, product.product_category, product.raw_code))
            self.conn.commit()
            self.cursor.execute('SELECT product_id FROM products WHERE product_code = ?', (product.product_code,))
            return product.product_code
        return None

    def close(self):
        self.conn.close()


def process_file(file_path, db):
    df = pd.read_excel(file_path, header=1)

    for index, row in df.iterrows():
        if pd.notna(row['毛坯料号']) and pd.notna(row['中文名称']):
            raw = Raw(row['毛坯料号'], row['中文名称'])
            raw_code = db.insert_raw(raw)

            if raw_code:
                for col in df.columns:
                    if col.startswith('商品编号'):
                        product_code = row[col]
                        if pd.notna(product_code):
                            product_category = df.at[index, '商品类别'] if '商品类别' in df.columns else None
                            product = Product(product_code, product_category, raw_code)
                            db.insert_product(product)


@log_execution
def preprocess_raw(file_path=f"./data/毛坯和成品对应表.xlsx", db_path="./database/longtai.db"):
    db = Database(db_path)
    process_file(file_path, db)
    db.close()


if __name__ == "__main__":
    preprocess_raw()
