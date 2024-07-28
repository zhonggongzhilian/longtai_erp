# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin

# Register your models here.
from .models import Product, Process, Order, OrderProduct, Device, Raw

admin.site.register(Product)
admin.site.register(Process)
admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(Device)
admin.site.register(Raw)