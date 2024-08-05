import logging

import pandas as pd
from django.db import transaction

from ..common.utils import log_execution
from ..models import Device

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_file(file_path):
    df = pd.read_excel(file_path, header=1)

    with transaction.atomic():
        for index, row in df.iterrows():
            if pd.notna(row['设备名称']):
                device_names = row['设备名称'].split('/')
                for device_name in device_names:
                    changeover_time = row['每次平均换型时间（分钟)']
                    print(f"{device_name=}, {changeover_time=}")
                    if not Device.objects.filter(device_name=device_name).exists():
                        Device.objects.create(
                            device_name=device_name.strip(),
                            changeover_time=str(changeover_time),
                            # 省略 user 字段，因为它可以为空
                        )
                    else:
                        device = Device.objects.get(device_name=device_name.strip())
                        device.exchange_time = str(changeover_time)
                        device.save()


@log_execution
def preprocess_device(file_path='../data/换型时间_MES.xlsx'):
    process_file(file_path)


if __name__ == '__main__':
    preprocess_device()
