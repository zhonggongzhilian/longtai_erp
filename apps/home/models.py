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
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长

    # 其他字段和方法


class Raw(models.Model):
    """
    毛坯模型
    """
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长
    raw_code = models.CharField(max_length=255, blank=True, null=True)
    raw_name = models.CharField(max_length=255, blank=True, null=True)
    raw_date_add = models.CharField(max_length=255, blank=True, null=True)
    raw_num = models.IntegerField(default=0)
    raw_weight = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.raw_code} - {self.raw_date_add}"


class Product(models.Model):
    """
    产品模型
    """
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长
    product_code = models.CharField(max_length=255, unique=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_kind = models.CharField(max_length=255, null=True, blank=True)
    raw_code = models.CharField(max_length=255, blank=True, null=True)
    weight = models.FloatField(null=True, blank=True, default=0.0)


class Device(models.Model):
    """
    设备模型
    """
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长
    device_name = models.CharField(max_length=255, unique=True)
    changeover_time = models.CharField(max_length=255, default="10")
    raw = models.CharField(max_length=255, blank=True, null=True)
    operators = models.ManyToManyField(CustomUser, related_name='operator_devices', blank=True)
    inspectors = models.ManyToManyField(CustomUser, related_name='inspector_devices', blank=True)

    start_time = models.DateTimeField(default=timezone.make_aware(datetime(1970, 1, 1)))
    end_time = models.DateTimeField(default=timezone.make_aware(datetime(1970, 1, 1)))
    is_fault = models.BooleanField(default=False)
    efficiency = models.FloatField(default=1.0)  # 生产效率值，默认为1

    def __str__(self):
        return self.device_name


class Order(models.Model):
    """
    订单模型
    """
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长
    order_code = models.CharField(max_length=255, blank=True, unique=True)  # 确保 order_code 是唯一的
    order_start_date = models.CharField(max_length=255, blank=True)
    order_end_date = models.CharField(max_length=255, blank=True)
    is_done = models.BooleanField(default=False)
    order_custom_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.order_code

    @classmethod
    def from_dataframe_rows(cls, order_row, products_rows):
        order = cls(
            order_code=order_row['订单编号'],
            order_start_date=order_row['订单日期'],
            order_end_date=order_row['交货日期'],
            order_custom_name=order_row['客户']
        )
        order.save()  # 保存订单
        products = [OrderProduct.from_dataframe_row(row, order) for _, row in products_rows.iterrows()]
        return order, products


class OrderProduct(models.Model):
    """
    订单中待产品信息
    """
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    product_code = models.CharField(max_length=255, blank=True)
    product_num_todo = models.IntegerField(default=0)
    product_num_done = models.IntegerField(default=0)
    cur_process_i = models.IntegerField(default=0)
    is_done = models.BooleanField(default=False)
    end_time = models.DateTimeField(default=timezone.make_aware(datetime(1970, 1, 1)))
    product_kind = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.order.order_code} - {self.product_code}"

    @classmethod
    def from_dataframe_row(cls, row, order):
        # 创建 OrderProduct 实例
        order_product = cls(
            order=order,
            product_code=row['商品编码'],
            product_num_todo=row['数量'],
            product_kind=row['商品类别']
        )
        order_product.save()  # 保存 OrderProduct 实例

        # 获取 '毛坯重量' 值
        raw_weight = row.get('销售单价', None)
        if raw_weight is not None:
            try:
                # 查找对应的 Product 实例
                product = Product.objects.get(product_code=row['商品编码'])
                raw_code = product.raw_code  # 获取对应的 raw_code
                if raw_code:
                    try:
                        # 查找对应的 Raw 实例
                        raw = Raw.objects.get(raw_code=raw_code)
                        # 更新 raw_weight 字段
                        raw.raw_weight = raw_weight
                        raw.save()
                    except Raw.DoesNotExist:
                        # 如果 Raw 实例不存在，可以选择创建一个新的 Raw 实例或记录日志
                        raw = Raw(raw_code=raw_code, raw_weight=raw_weight, raw_name='')
                        raw.save()
                else:
                    # 如果 product 的 raw_code 为空，记录日志或采取其他操作
                    pass
            except Product.DoesNotExist:
                # 如果 Product 实例不存在，可以选择创建一个新的 Product 实例或记录日志
                pass
        return order_product


class Process(models.Model):
    """
    工序模型
    """
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长
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
    id = models.AutoField(primary_key=True)  # 默认行为是自动增长
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
    product_num_completed = models.IntegerField(default=0, null=True)
    product_num_inspected = models.IntegerField(default=0, null=True)

    class Meta:
        verbose_name = 'Order Processing Result'
        verbose_name_plural = 'Order Processing Results'

    def __str__(self):
        return f"Order {self.order_code}, Product {self.product_code}, Process {self.process_i}"


class Weight(models.Model):
    weight = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.weight}"
