# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),

    path('upload', views.upload, name='upload'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_id>/products/', views.order_product_list, name='order_product_list'),
    path('orders/<str:order_id>/get/', views.get_order, name='get_order'),
    path('orders/<str:order_id>/update/', views.update_order, name='update_order'),
    path('orders/<str:order_id>/delete/', views.delete_order, name='delete_order'),

    path('exchanges/', views.exchange_list, name='exchange_list'),
    path('exchanges/<int:exchange_id>/get/', views.get_exchange, name='get_exchange'),
    path('exchanges/<int:exchange_id>/update/', views.update_exchange, name='update_exchange'),
    path('exchanges/<int:exchange_id>/delete/', views.delete_exchange, name='delete_exchange'),

    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/get/', views.get_product, name='get_product'),
    path('products/<int:product_id>/update/', views.update_product, name='update_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
]
