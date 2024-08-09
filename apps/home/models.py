from django.contrib.auth.models import AbstractUser

from django.db import models

from django.utils import timezone

from datetime import datetime


class CustomUser(AbstractUser):
    """
    自定义用户模型
    """
    # 定义角色选项
    OPERATOR = 'operator'
    INSPECTOR = 'inspector'
    ADMIN = 'admin'
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    ROLE_CHOICES = [
        (OPERATOR, '操作员'),
        (INSPECTOR, '质检员'),
        (ADMIN, '管理员'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=OPERATOR,
    )

    # 其他字段和方法


class Raw(models.Model):
    """
    毛坯模型
    """
    raw_code = models.CharField(max_length=255, unique=True)
    raw_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.raw_code


class Product(models.Model):
    """
    产品模型
    """
    product_code = models.CharField(max_length=255, unique=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_kind = models.CharField(max_length=255, null=True, blank=True)
    raw_code = models.CharField(max_length=255, blank=True, null=True)
    weight = models.FloatField(null=True, blank=True, default=0.0)


class Device(models.Model):
    """
    设备模型
    """
    device_name = models.CharField(max_length=255, unique=True)
    changeover_time = models.CharField(max_length=255, default="10")
    raw = models.CharField(max_length=255, blank=True, null=True)
    operator = models.ForeignKey(CustomUser, related_name='operator_devices', null=True, blank=True,
                                 on_delete=models.SET_NULL)
    inspector = models.ForeignKey(CustomUser, related_name='inspector_devices', null=True, blank=True,
                                  on_delete=models.SET_NULL)

    start_time = models.DateTimeField(default=timezone.make_aware(datetime(1970, 1, 1)))
    end_time = models.DateTimeField(default=timezone.make_aware(datetime(1970, 1, 1)))

    def __str__(self):
        return self.device_name


class Order(models.Model):
    """
    订单模型
    """
    order_code = models.CharField(max_length=255, blank=True, unique=True)  # 确保 order_code 是唯一的
    order_start_date = models.CharField(max_length=255, blank=True)
    order_end_date = models.CharField(max_length=255, blank=True)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return self.order_code

    @classmethod
    def from_dataframe_rows(cls, order_row, products_rows):
        order = cls(
            order_code=order_row['订单编号'],
            order_start_date=order_row['订单日期'],
            order_end_date=order_row['交货日期']
        )
        order.save()  # 保存订单
        products = [OrderProduct.from_dataframe_row(row, order) for _, row in products_rows.iterrows()]
        return order, products


class OrderProduct(models.Model):
    """
    订单中待产品信息
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    product_code = models.CharField(max_length=255, blank=True)
    product_num_todo = models.IntegerField(default=0)
    product_num_done = models.IntegerField(default=0)
    cur_process_i = models.IntegerField(default=0)
    is_done = models.BooleanField(default=False)
    end_time = models.DateTimeField(default=timezone.make_aware(datetime(1970, 1, 1)))

    def __str__(self):
        return f"{self.order.order_code} - {self.product_code}"

    @classmethod
    def from_dataframe_row(cls, row, order):
        product = cls(
            order=order,
            product_code=row['商品编码'],
            product_num_todo=row['数量']
        )
        product.save()  # 保存产品
        return product


class Process(models.Model):
    """
    工序模型
    """
    process_i = models.IntegerField(default=1)
    process_name = models.CharField(max_length=255)
    process_capacity = models.IntegerField(null=True, blank=True, default=0)
    process_duration = models.FloatField(null=True, blank=True, default=0.0)
    product_code = models.CharField(max_length=255, null=True, blank=True)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    is_outside = models.BooleanField(default=False)
    is_last_process = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.process_name}-{self.process_i}"


class Task(models.Model):
    task_start_time = models.DateTimeField(default=timezone.now)  # 使用带时区的时间
    task_end_time = models.DateTimeField(default=timezone.now)  # 使用带时区的时间
    is_changeover = models.CharField(max_length=3, default='No')
    order_code = models.CharField(max_length=20, default='')
    product_code = models.CharField(max_length=20, default='')
    process_i = models.PositiveIntegerField(default=0)
    process_name = models.CharField(max_length=100, default='')
    device_name = models.CharField(max_length=100, default='')
    completed = models.BooleanField(default=False)
    inspected = models.BooleanField(default=False)
    product_num = models.IntegerField(default=0, null=True)

    class Meta:
        verbose_name = 'Order Processing Result'
        verbose_name_plural = 'Order Processing Results'

    def __str__(self):
        return f"Order {self.order_code}, Product {self.product_code}, Process {self.process_i}"


class Weight(models.Model):
    weight = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.weight}"