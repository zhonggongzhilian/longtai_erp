import logging
import sqlite3

import pandas as pd

from ..common.utils import log_execution

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_type_time (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT,
            exchange_time TEXT,
            current_raw TEXT
        )
        ''')
        self.conn.commit()

    def insert_data(self, device_name, exchange_time):
        self.cursor.execute('''
        INSERT INTO exchange_type_time (device_name, exchange_time)
        VALUES (?, ?)
        ''', (device_name, exchange_time))
        self.conn.commit()

    def close(self):
        self.conn.close()


def process_file(file_path, db_path):
    df = pd.read_excel(file_path, header=1)
    db = Database(db_path)

    for index, row in df.iterrows():
        if pd.notna(row['设备名称']):
            device_names = row['设备名称'].split('/')
            for device_name in device_names:
                db.insert_data(device_name, row['每次平均换型时间（分钟)'])

    db.close()


@log_execution
def preprocess_exchange(file_path='../data/换型时间_MES.xlsx', db_path='../database/longtai.db'):
    process_file(file_path, db_path)


if __name__ == '__main__':
    preprocess_exchange()
