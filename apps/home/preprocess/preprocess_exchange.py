import logging

import pandas as pd
from django.db import transaction

from ..common.utils import log_execution
from ..models import ExchangeTypeTime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_file(file_path):
    df = pd.read_excel(file_path, header=1)

    with transaction.atomic():
        for index, row in df.iterrows():
            if pd.notna(row['设备名称']):
                device_names = row['设备名称'].split('/')
                for device_name in device_names:
                    exchange_time = row['每次平均换型时间（分钟)']
                    if not ExchangeTypeTime.objects.filter(device_name=device_name).exists():
                        ExchangeTypeTime.objects.create(
                            device_name=device_name.strip(),
                            exchange_time=str(exchange_time)
                        )
                    else:
                        exchange_type_time = ExchangeTypeTime.objects.get(device_name=device_name.strip())
                        exchange_type_time.exchange_time = str(exchange_time)
                        exchange_type_time.save()


@log_execution
def preprocess_exchange(file_path='../data/换型时间_MES.xlsx'):
    process_file(file_path)


if __name__ == '__main__':
    preprocess_exchange()
