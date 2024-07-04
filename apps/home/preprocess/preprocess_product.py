import logging
import sqlite3
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def add_column_if_not_exists(cursor, table_name, column_name, column_type="TEXT"):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def insert_or_update_product(cursor, product_code, weight):
    cursor.execute('SELECT product_id FROM products WHERE product_code = ?', (product_code,))
    row = cursor.fetchone()
    if row:
        cursor.execute('UPDATE products SET weight = ? WHERE product_code = ?', (weight, product_code))
        logger.info(f"Updated product {product_code} with weight {weight}")
    else:
        cursor.execute('INSERT INTO products (product_code, weight) VALUES (?, ?)', (product_code, weight))


def update_product_weights(cursor, weights):
    # 如果表中没有Weight列，添加Weight列
    add_column_if_not_exists(cursor, 'products', 'weight', 'REAL')

    # 插入或更新产品重量
    for product_code, weight in weights.items():
        insert_or_update_product(cursor, product_code, weight)


def load_weight_data(file_path):
    # 读取 Excel 文件
    df = pd.read_excel(file_path)

    # 转换为字典
    weights = dict(zip(df['PartNumber零件号码'], df['Weight重量(kg)']))
    return weights


def preprocess_product(file_path, db_path='../database/longtai.db'):
    # 加载重量数据
    weights = load_weight_data(file_path)

    # 连接 SQLite 数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 更新产品重量
    update_product_weights(cursor, weights)

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

    logger.info("Done updating product weights")


if __name__ == "__main__":
    weight_file_path = '../data/净重.xlsx'
    preprocess_product(weight_file_path)