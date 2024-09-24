# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.home import views
from .views import device_list, ProcessListView, AddProcessView, clear_schedule

urlpatterns = [

    path('login/', views.login_view, name="login"),
    path('register/', views.register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path('', views.index, name='home'),

    path('upload', views.upload, name='upload'),

    path('orders/', views.order_list, name='order_list'),

    path('device/', device_list, name='device_list'),
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
    path('results/process_schedule_fast/', views.process_schedule_fast, name='process_orders_fast'),
    path('results/process_schedule/', views.process_schedule, name='process_orders'),
    path('get_progress/', views.get_progress, name='get_progress'),

    path('users/', views.user_list_list, name='user_list_list'),
    path('users/<int:user_id>/get/', views.user_list_get, name='user_list_get'),
    path('users/<int:user_id>/update/', views.user_list_update, name='user_list_update'),
    path('users/<int:user_id>/delete/', views.user_list_delete, name='user_list_delete'),
    path('users/create/', views.user_list_create, name='user_list_create'),

    # My tasks
    path('filter_by_date/', views.filter_by_date, name='filter_by_date'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('my_tasks_done/', views.my_tasks_done, name='my_tasks_done'),
    path('tasks/filter_by_date/', views.filter_by_date, name='filter_by_date'),
    path('my_tasks_operator_detail/<int:task_id>/', views.my_tasks_operator_detail, name='my_tasks_operator_detail'),
    path('my_tasks_operator_complete_task/', views.my_tasks_operator_complete_task,
         name='my_tasks_operator_complete_task'),
    path('my_tasks_operator_rework_task/', views.my_tasks_operator_rework_task, name='my_tasks_operator_rework_task'),
    path('my_tasks_operator_scrap_task/', views.my_tasks_operator_scrap_task, name='my_tasks_operator_scrap_task'),


    path('my_tasks_inspector_detail/<int:task_id>/', views.my_tasks_inspector_detail, name='my_tasks_inspector_detail'),
    path('my_tasks_inspector_complete_task/', views.my_tasks_inspector_complete_task,
         name='my_tasks_inspector_complete_task'),
    path('my_tasks_inspector_complete_tasks/', views.my_tasks_inspector_complete_tasks,
         name='my_tasks_inspector_complete_tasks'),
    path('my_tasks_inspector_scrap_tasks/', views.my_tasks_inspector_scrap_tasks, name='my_tasks_inspector_scrap_tasks'),
    path('my_tasks_operator_one_btn_complete_tasks/', views.my_tasks_operator_one_btn_complete_tasks, name='my_tasks_operator_one_btn_complete_tasks'),

    path('tasks/add-urgent/', views.add_urgent_task, name='add_urgent_task'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('create-order/', views.create_order, name='create_order'),

    path('schedule-by-date/', views.schedule_by_date, name='schedule_by_date'),

    path('processes/', ProcessListView.as_view(), name='process-list'),
    path('processes/add/', AddProcessView.as_view(), name='add_process'),

    path('clear_schedule/', clear_schedule, name='clear_schedule'),
    path('process/<int:process_id>/get/', views.get_process, name='get_process'),
    path('process/<int:process_id>/update/', views.update_process, name='update_process'),
    path('process/<int:process_id>/delete/', views.delete_process, name='delete_process'),
]
