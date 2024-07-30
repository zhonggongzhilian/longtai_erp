# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.home import views

urlpatterns = [

    path('login/', views.login_view, name="login"),
    path('register/', views.register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path('', views.index, name='home'),

    path('upload', views.upload, name='upload'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_id>/products/', views.order_product_list, name='order_product_list'),
    path('orders/<str:order_id>/get/', views.get_order, name='get_order'),
    path('orders/<str:order_id>/update/', views.update_order, name='update_order'),
    path('orders/<str:order_id>/delete/', views.delete_order, name='delete_order'),

    path('device/', views.device_list, name='device_list'),
    path('device/<int:device_id>/get/', views.get_device, name='get_device'),
    path('device/<int:device_id>/update/', views.update_device, name='update_device'),
    path('device/<int:device_id>/delete/', views.delete_device, name='delete_device'),

    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/get/', views.get_product, name='get_product'),
    path('products/<int:product_id>/update/', views.update_product, name='update_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),

    path('raws/', views.raw_list, name='raw_list'),
    path('raws/<int:pk>/get/', views.raw_get, name='raw_get'),
    path('raws/<int:pk>/update/', views.raw_update, name='raw_update'),
    path('raws/<int:pk>/delete/', views.raw_delete, name='raw_delete'),

    path('results/', views.result_list, name='result_list'),
    path('results/<int:result_id>/delete/', views.delete_result, name='delete_result'),
    path('results/process_schedule/', views.process_schedule, name='process_orders'),

    path('users/', views.user_list_list, name='user_list_list'),
    path('users/<int:user_id>/get/', views.user_list_get, name='user_list_get'),
    path('users/<int:user_id>/update/', views.user_list_update, name='user_list_update'),
    path('users/<int:user_id>/delete/', views.user_list_delete, name='user_list_delete'),
    path('users/create/', views.user_list_create, name='user_list_create'),

    path('filter_by_date/', views.filter_by_date, name='filter_by_date'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('tasks/filter_by_date/', views.filter_by_date, name='filter_by_date'),
    path('tasks/<int:id>/mark-complete/', views.mark_complete, name='mark_complete'),
    path('tasks/<int:id>/mark-not-complete/', views.mark_not_complete, name='mark_complete'),
    path('tasks/<int:id>/mark-inspected/', views.mark_inspected, name='mark_inspected'),
    path('tasks/<int:id>/mark-not-inspected/', views.mark_not_inspected, name='mark_inspected'),

    path('tasks/add-urgent/', views.add_urgent_task, name='add_urgent_task'),
]
