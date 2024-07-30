import pandas as pd

from django.contrib.auth.models import AbstractUser

from django.db import models


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
        (OPERATOR, 'Operator'),
        (INSPECTOR, 'Inspector'),
        (ADMIN, 'Administrator'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=OPERATOR,
    )

    # 其他字段和方法


class Device(models.Model):
    """
    设备模型
    """
    device_name = models.CharField(max_length=255, unique=True)
    exchange_time = models.CharField(max_length=255)
    raw = models.CharField(max_length=255, blank=True, null=True)
    operator = models.ForeignKey(CustomUser, related_name='operator_devices', null=True, blank=True,
                                 on_delete=models.SET_NULL)
    inspector = models.ForeignKey(CustomUser, related_name='inspector_devices', null=True, blank=True,
                                  on_delete=models.SET_NULL)

    def __str__(self):
        return self.device_name


class Order(models.Model):
    """
    订单模型
    """
    order_id = models.CharField(max_length=255, primary_key=True)
    order_date = models.CharField(max_length=255)
    associate_sale_id = models.CharField(max_length=255, blank=True, null=True)
    business_kind = models.CharField(max_length=255, blank=True, null=True)
    associate_purchase_order_id = models.CharField(max_length=255, blank=True, null=True)
    saler = models.CharField(max_length=255, blank=True, null=True)
    customer = models.CharField(max_length=255, blank=True, null=True)
    sale_amount = models.FloatField()
    discount_price = models.FloatField()
    discounted_price = models.FloatField()
    order_state = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.CharField(max_length=255)
    order_maker = models.CharField(max_length=255, blank=True, null=True)
    order_making_time = models.CharField(max_length=255, blank=True, null=True)
    reviewer = models.CharField(max_length=255, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    delivery_method = models.CharField(max_length=255, blank=True, null=True)
    print_count = models.IntegerField(blank=True, null=True)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.order_id

    @classmethod
    def from_dataframe_rows(cls, order_row, products_rows):
        order = cls(
            order_id=order_row['订单编号'],
            order_date=order_row['订单日期'],
            associate_sale_id=order_row['关联销货单号'],
            business_kind=order_row['业务类别'],
            associate_purchase_order_id=order_row['关联购货订单号'],
            saler=order_row['销售人员'],
            customer=order_row['客户'],
            sale_amount=order_row['销售金额'],
            discount_price=order_row['优惠金额'],
            discounted_price=order_row['优惠后金额'],
            order_state=order_row['订单状态'],
            delivery_date=order_row['交货日期'],
            order_maker=order_row['制单人'],
            order_making_time=order_row['制单时间'],
            reviewer=order_row['审核人'],
            remark=order_row['备注'],
            delivery_method=order_row['交货方式'],
            print_count=order_row['打印次数'] if not pd.isna(order_row['打印次数']) else None,
        )
        order.save()  # 保存订单
        products = [OrderProduct.from_dataframe_row(row, order) for _, row in products_rows.iterrows()]
        return order, products


class OrderProduct(models.Model):
    """
    订单产品信息
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_code = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    product_model = models.CharField(max_length=255)
    attribute = models.CharField(max_length=255, blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    product_remark = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField()
    sale_price = models.FloatField()
    estimated_purchase_price = models.FloatField(blank=True, null=True)
    discount_rate = models.FloatField(blank=True, null=True)
    discount_amount = models.FloatField(blank=True, null=True)
    discount = models.FloatField(blank=True, null=True)
    discounted_price = models.FloatField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    reference_cost = models.FloatField(blank=True, null=True)
    estimated_gross_profit = models.FloatField(blank=True, null=True)
    estimated_gross_profit_rate = models.FloatField(blank=True, null=True)
    latest_purchase_price = models.FloatField(blank=True, null=True)
    product_house = models.CharField(max_length=255, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    available_stock = models.IntegerField(blank=True, null=True)
    basic_unit = models.CharField(max_length=255, blank=True, null=True)
    basic_unit_quantity = models.IntegerField(blank=True, null=True)
    whole_scatter = models.CharField(max_length=255, blank=True, null=True)
    conversion_formula = models.CharField(max_length=255, blank=True, null=True)
    is_gift = models.BooleanField(default=False)
    shelf = models.CharField(max_length=255, blank=True, null=True)
    undelivered_quantity = models.IntegerField(blank=True, null=True)
    undelivered_basic_quantity = models.IntegerField(blank=True, null=True)
    delivered_quantity = models.IntegerField(blank=True, null=True)
    delivered_basic_quantity = models.IntegerField(blank=True, null=True)
    row_status = models.CharField(max_length=255, blank=True, null=True)
    custom_column_one = models.CharField(max_length=255, blank=True, null=True)
    custom_column_two = models.CharField(max_length=255, blank=True, null=True)
    custom_column_three = models.CharField(max_length=255, blank=True, null=True)
    custom_column_four = models.CharField(max_length=255, blank=True, null=True)
    custom_column_five = models.CharField(max_length=255, blank=True, null=True)
    done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.order.order_id} - {self.product_code}"

    @classmethod
    def from_dataframe_row(cls, row, order):
        product = cls(
            order=order,
            product_code=row['商品编码'],
            product_name=row['商品名称'],
            product_model=row['商品型号'],
            attribute=row['属性'],
            barcode=row['商品条码'],
            category=row['商品类别'],
            product_remark=row['商品备注'],
            unit=row['单位'],
            quantity=row['数量'],
            sale_price=row['销售单价'],
            estimated_purchase_price=row['预计采购价'] if not pd.isna(row['预计采购价']) else None,
            discount_rate=row['折扣率(%)'] if not pd.isna(row['折扣率(%)']) else None,
            discount_amount=row['折扣额'] if not pd.isna(row['折扣额']) else None,
            discount=row['折扣(折)'] if not pd.isna(row['折扣(折)']) else None,
            discounted_price=row['折后单价'] if not pd.isna(row['折后单价']) else None,
            amount=row['金额'] if not pd.isna(row['金额']) else None,
            reference_cost=row['参考成本'] if not pd.isna(row['参考成本']) else None,
            estimated_gross_profit=row['预估毛利'] if not pd.isna(row['预估毛利']) else None,
            estimated_gross_profit_rate=row['预估毛利率%'] if not pd.isna(row['预估毛利率%']) else None,
            latest_purchase_price=row['最近一次采购价'] if not pd.isna(row['最近一次采购价']) else None,
            product_house=row['仓库'],
            remark=row['备注.1'],
            available_stock=row['可用库存'] if not pd.isna(row['可用库存']) else None,
            basic_unit=row['基本单位'],
            basic_unit_quantity=row['基本单位数量'] if not pd.isna(row['基本单位数量']) else None,
            whole_scatter=row['整件散包'],
            conversion_formula=row['换算公式'],
            is_gift=row['是否赠品'] == '是',
            shelf=row['货架'],
            undelivered_quantity=row['未出库数量'] if not pd.isna(row['未出库数量']) else None,
            undelivered_basic_quantity=row['未出库基本数量'] if not pd.isna(row['未出库基本数量']) else None,
            delivered_quantity=row['已出库数量'] if not pd.isna(row['已出库数量']) else None,
            delivered_basic_quantity=row['已出库基本数量'] if not pd.isna(row['已出库基本数量']) else None,
            row_status=row['行状态'],
            custom_column_one=row['自定义列一'],
            custom_column_two=row['自定义列二'],
            custom_column_three=row['自定义列三'],
            custom_column_four=row['自定义列四'],
            custom_column_five=row['自定义列五'],
        )
        product.save()  # 保存产品
        return product


class Raw(models.Model):
    """
    毛坯模型
    """
    raw_code = models.CharField(max_length=255, unique=True)
    raw_name = models.CharField(max_length=255)

    def __str__(self):
        return self.raw_code


class Product(models.Model):
    """
    产品模型
    """
    product_code = models.CharField(max_length=255, unique=True)
    product_category = models.CharField(max_length=255, null=True, blank=True)
    raw = models.ForeignKey('Raw', on_delete=models.SET_NULL, null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, default=0.0)


class Process(models.Model):
    """
    工序模型
    """
    product_code = models.ForeignKey("Product", on_delete=models.CASCADE, null=True, blank=True)
    process_sequence = models.IntegerField(default=1)
    process_name = models.CharField(max_length=255)
    quantity = models.IntegerField(null=True, blank=True, default=0)
    duration = models.FloatField(null=True, blank=True, default=0.0)
    equipment = models.CharField(max_length=255, null=True, blank=True, default='')
    completion_date = models.CharField(max_length=255, null=True, blank=True, default='')
    done = models.BooleanField(default=False)
    last_process = models.BooleanField(default=False)


from django.db import models

from django.utils import timezone


class OrderProcessingResult(models.Model):
    execution_time = models.DateTimeField(default=timezone.now)  # 使用带时区的时间
    completion_time = models.DateTimeField(default=timezone.now)  # 使用带时区的时间
    changeover = models.CharField(max_length=3, default='No')
    order = models.CharField(max_length=20, default='')
    product = models.CharField(max_length=20, default='')
    process_sequence = models.PositiveIntegerField(default=0)
    process_name = models.CharField(max_length=100, default='')
    device = models.CharField(max_length=100, default='')
    completed = models.BooleanField(default=False)
    inspected = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Order Processing Result'
        verbose_name_plural = 'Order Processing Results'

    def __str__(self):
        return f"Order {self.order}, Product {self.product}, Process {self.process_sequence}"
