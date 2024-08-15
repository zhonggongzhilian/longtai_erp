# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import logging
import os
from datetime import datetime, timedelta
from io import BytesIO

import pytz
from django import template
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from .forms import CustomUserChangeForm
from .models import Device, CustomUser
from .models import Order, OrderProduct
from .models import Process, Raw, Product
from .models import Task  # 确保导入你的 Task 模型
from .models import Weight
from .preprocess import preprocess_order, preprocess_product, preprocess_process, preprocess_device, preprocess_raw
from .views_login import login_view, register_user

__all__ = [login_view, register_user]

# views.py

logger = logging.getLogger(__name__)


def user_list_list(request):
    users = CustomUser.objects.all()
    return render(request, 'home/user_list.html', {'users': users})


def user_list_get(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    data = {
        'username': user.username,
        'phone_number': user.phone_number,
        'role': user.role,
    }
    return JsonResponse(data)


@csrf_exempt
def user_list_update(request, user_id):
    print(f"user list update !")
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'status': 'error', 'errors': errors})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@csrf_exempt
def user_list_delete(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        user.delete()
        return JsonResponse({'status': 'success'})


@csrf_exempt
@login_required
def user_list_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone_number = request.POST.get('phone_number')
        role = request.POST.get('role')

        if password1 != password2:
            return JsonResponse({'error': 'Passwords do not match.'}, status=400)

        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists.'}, status=400)

        try:
            user = CustomUser.objects.create_user(username=username, password=password1, phone_number=phone_number,
                                                  role=role)
            # You can add extra logic to save phone_number and role in a custom user profile model
            user.save()
            # Optionally log in the user after creation
            # user = authenticate(username=username, password=password1)
            # if user is not None:
            #     login(request, user)
            return JsonResponse({'success': 'User created successfully.'})
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred while creating the user.'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)


@login_required(login_url="/login/")
def index(request):
    orders_count = Order.objects.count()
    products_count = Product.objects.count()
    raw_count = Raw.objects.count()
    exchange_count = Device.objects.count()
    process_count = Process.objects.count()
    # 获取最新的 weight 数据
    weight = Weight.objects.latest('id').weight  # 根据你的模型字段名获取 weight

    context = {
        'segment': 'index',
        'orders_count': orders_count,
        'products_count': products_count,
        'raw_count': raw_count,
        'exchange_count': exchange_count,
        'process_count': process_count,
        'weight': weight,
    }

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template
        logger.info(f"{load_template=}")
        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


def _upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_type = request.POST.get('file_type')
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)

        file_path = os.path.join(fs.location, filename)

        try:
            if file_type == 'orders':
                preprocess_order(file_path)
            elif file_type == 'raw':
                preprocess_raw(file_path)
            elif file_type == 'process':
                preprocess_process(file_path)
            elif file_type == 'product':
                preprocess_product(file_path)
            elif file_type == 'exchange':
                preprocess_device(file_path)
            else:
                return JsonResponse({"error": "Unknown file type."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)

        return JsonResponse({"message": "File uploaded and processed successfully."})

    return render(request, 'home/index.html')


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        try:
            file_type = request.POST.get('file_type')
            file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = os.path.join(fs.location, filename)

            if file_type == 'orders':
                preprocess_order(file_path)
            elif file_type == 'raw':
                preprocess_raw(file_path)
            elif file_type == 'process':
                preprocess_process(file_path)
            elif file_type == 'product':
                preprocess_product(file_path)
            elif file_type == 'exchange':
                preprocess_device(file_path)
            else:
                raise ValueError("Invalid file type.")

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(str(e), exc_info=True)  # 记录详细的错误信息
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def order_list(request):
    order_products = OrderProduct.objects.select_related('order').all()
    context = {
        'order_products': order_products,
    }
    return render(request, 'home/order_list.html', context)


def get_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    data = {
        'order_id': order.order_id,
        'order_date': order.order_start_date,
        'customer': order.customer,
        'sale_amount': order.sale_amount,
        'order_state': order.order_state,
    }
    return JsonResponse(data)


def update_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id)
        order.order_start_date = request.POST.get('order_date')
        order.customer = request.POST.get('customer')
        order.sale_amount = request.POST.get('sale_amount')
        order.order_state = request.POST.get('order_state')
        order.save()
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def delete_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id)
        OrderProduct.objects.filter(order=order).delete()  # 删除相关的 OrderProduct
        order.delete()
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def device_list(request):
    devices = Device.objects.all()
    return render(request, 'home/device_list.html', {'devices': devices})


def get_device(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    data = {
        'device_name': device.device_name,
        'changeover_time': device.changeover_time,
        'operator': device.operator.id if device.operator else None,
        'inspector': device.inspector.id if device.inspector else None,
    }
    return JsonResponse(data)


def update_device(request, device_id):
    if request.method == 'POST':
        device = get_object_or_404(Device, id=device_id)
        device.device_name = request.POST.get('device_name')
        device.exchange_time = request.POST.get('exchange_time')
        # Update operator and inspector fields
        device.operator_id = request.POST.get('operator')
        device.inspector_id = request.POST.get('inspector')
        device.save()
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def delete_device(request, device_id):
    if request.method == 'POST':
        device = get_object_or_404(Device, id=device_id)
        device.delete()
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def product_list(request):
    products = Product.objects.all()
    per_page = request.GET.get('per_page', 20)  # 获取用户自定义的每页数量，默认为20
    paginator = Paginator(products, per_page)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 处理产品列表，添加原料代码
    product_list = []
    for product in page_obj:
        product_list.append({
            'product_code': product.product_code,
            'product_name': product.product_name,
            'product_kind': product.product_kind,
            'raw_code': product.raw_code,
            'weight': product.weight
        })

    context = {
        'products': product_list,
        'page_obj': page_obj,
        'per_page': per_page
    }
    return render(request, 'home/product_list.html', context)


def get_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    data = {
        'product_code': product.product_code,
        'product_category': product.product_category,
        'raw': product.raw_code.raw_code if product.raw_code else None,
    }
    return JsonResponse(data)


def update_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.product_code = request.POST.get('product_code')
        product.product_category = request.POST.get('product_category')
        raw_code = request.POST.get('raw')
        if raw_code:
            product.raw_code = get_object_or_404(Raw, raw_code=raw_code)
        else:
            product.raw_code = None
        product.save()
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def delete_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def raw_list(request):
    raws = Raw.objects.all()
    paginator = Paginator(raws, request.GET.get('per_page', 20))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'raws': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'per_page': request.GET.get('per_page', 20)
    }
    return render(request, 'home/raw_list.html', context)


def raw_get(request, pk):
    raw = get_object_or_404(Raw, pk=pk)
    data = {
        'raw_code': raw.raw_code,
        'raw_name': raw.raw_name,
    }
    return JsonResponse(data)


def raw_update(request, pk):
    raw = get_object_or_404(Raw, pk=pk)
    if request.method == 'POST':
        raw.raw_code = request.POST.get('raw_code')
        raw.raw_name = request.POST.get('raw_name')
        raw.save()
        return JsonResponse({'success': True})


def raw_delete(request, pk):
    raw = get_object_or_404(Raw, pk=pk)
    if request.method == 'POST':
        raw.delete()
        return JsonResponse({'success': True})


def result_list(request):
    results = Task.objects.all()
    return render(request, 'home/result_list.html', {'results': results})


def get_progress(request):
    try:
        with open('./progress.txt', 'r') as f:
            progress = f.read()
    except FileNotFoundError:
        progress = '0'
    return JsonResponse({'progress': progress})


def delete_result(request, result_id):
    if request.method == 'POST':
        result = Task.objects.get(id=result_id)
        result.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def process_schedule_fast(request):
    from .job_scheduler_1 import schedule_production
    if request.method == 'POST':
        Task.objects.all().delete()  # 清空 OrderProcessingResult 表
        schedule_production(fast=True)  # 重新计算排产结果
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def process_schedule(request):
    from .job_scheduler_1 import schedule_production
    if request.method == 'POST':
        Task.objects.all().delete()  # 清空 OrderProcessingResult 表
        schedule_production()  # 重新计算排产结果
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@csrf_exempt
def filter_by_date(request):
    if request.method == 'GET':
        date_str = request.GET.get('date', '2023-05-01')
        selected_date = parse_date(date_str)
        if selected_date:
            # Convert to local timezone if needed
            local_tz = pytz.timezone('Asia/Shanghai')  # Replace with your local timezone
            start_datetime = local_tz.localize(datetime.combine(selected_date, datetime.min.time()))
            end_datetime = start_datetime + timedelta(days=1)

            # Filter results within the selected date
            results = Task.objects.filter(
                execution_time__range=(start_datetime, end_datetime)
            ).values()

            return JsonResponse({'results': list(results)})
        return JsonResponse({'results': []})


def mark_complete(request, id):
    task = Task.objects.get(pk=id)
    task.completed = True
    task.save()
    return JsonResponse({'success': True})


def mark_not_complete(request, id):
    task = Task.objects.get(pk=id)
    if task:
        task.completed = False
        task.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


def mark_inspected(request, id):
    task = Task.objects.get(pk=id)
    task.inspected = True
    task.save()
    return JsonResponse({'success': True})


def mark_not_inspected(request, id):
    task = Task.objects.get(pk=id)
    if task:
        task.inspected = False
        task.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@require_POST
@csrf_exempt
def add_urgent_task(request):
    task_start_time = request.POST.get('task_start_time')
    task_end_time = request.POST.get('task_end_time')
    order_code = request.POST.get('order_code')
    product_code = request.POST.get('product_code')
    process_i = request.POST.get('process_i')
    process_name = request.POST.get('process_name')
    device_name = request.POST.get('device_name')

    task = Task.objects.create(
        task_start_time=task_start_time,
        task_end_time=task_end_time,
        order_code=order_code,
        product_code=product_code,
        process_i=process_i,
        process_name=process_name,
        device_name=device_name,
        completed=False,
        inspected=False
    )

    return JsonResponse({'success': True, 'task_id': task.id})


# My tasks

@login_required
def my_tasks(request):
    user = request.user
    if user.role == 'admin':
        # Admins see all results
        tasks = Task.objects.all().order_by('task_start_time')
    elif user.role == 'inspector':
        related_device_names = Device.objects.filter(inspector=user).values_list('device_name', flat=True)
        tasks = Task.objects.filter(
            device_name__in=related_device_names,
            completed=1,
        ).order_by('task_start_time')
    else:
        # Operators and Inspectors see only related tasks
        related_device_names = Device.objects.filter(
            operator=user
        ).values_list('device_name', flat=True)
        tasks = Task.objects.filter(
            device_name__in=related_device_names
        ).order_by('task_start_time')

    import qrcode  # 用于生成二维码
    # 获取当前页面的完整 URL
    current_url = request.build_absolute_uri()

    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(current_url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    # 保存二维码图片到文件系统
    img_path = 'apps/static/assets/img/qrcode/my_tasks_qr.png'
    img.save(img_path)

    context = {
        'tasks': tasks,
        'user': user,
        'qr_code_url': img_path,
    }
    return render(request, 'home/my_tasks.html', context)


def my_tasks_operator_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'home/my_tasks_operator_detail.html', {'task': task})


def is_max_process(order_product):
    """
    判断当前工序是否是订单产品的最大工序。
    """
    all_processes = Process.objects.filter(product_code=order_product.product_code).order_by('process_i')
    process_indices = [p.process_i for p in all_processes]
    max_process_i = max(process_indices)
    return order_product.cur_process_i == max_process_i


@csrf_exempt
def my_tasks_operator_complete_task(request):
    if request.method == 'POST':
        # Update OrderProduct
        task_id = request.POST.get('task_id')
        product_num = request.POST.get('product_num')
        print(f"{product_num=}")

        task = Task.objects.get(id=task_id)
        order_code = task.order_code
        order = get_object_or_404(Order, order_code=order_code)

        product_code = task.product_code
        order_product = OrderProduct.objects.get(product_code=product_code,
                                                 order=order)
        print(f"{task.product_num_completed=}")
        task.product_num_completed += int(product_num)
        if task.product_num_completed >= task.product_num:
            task.completed = 1

        print(f"{task.product_num_completed=}")
        task.save()

        if is_max_process(order_product):
            order_product.product_num_done += product_num
            order_product.product_num_todo -= product_num
            if order_product.product_num_todo <= 0:
                order_product.is_done = 1
            order_product.save()

            # Update Order
            order = order_product.order
            if not OrderProduct.objects.filter(order=order, is_done=0).exists():
                order.is_done = 1
            order.save()

            # Update Weight
            product = Product.objects.get(code=order_product.product_code)
            weight = Weight.objects.get(product=product)
            weight.weight += product.weight * product_num
            weight.save()

        return JsonResponse({'success': True,
                             'product_num': task.product_num, })
    return JsonResponse({'success': False})


@csrf_exempt
def my_tasks_operator_rework_task(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')

        rework_product_num = int(request.POST.get('product_num_2'))

        try:
            # Get the OrderProduct instance
            task = Task.objects.get(id=task_id)
            task.product_num_completed -= rework_product_num
            task.product_num_inspected -= rework_product_num
            task.completed = 0
            task.inspected = 0
            task.save()
            order_code = task.order_code
            order = get_object_or_404(Order, order_code=order_code)

            product_code = task.product_code
            order_product = OrderProduct.objects.get(product_code=product_code,
                                                     order=order)

            # Decrement cur_process_i
            if order_product.cur_process_i > 0:
                order_product.cur_process_i -= 1
                order_product.save()

            return JsonResponse({'success': True})
        except OrderProduct.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'OrderProduct not found'})

    return JsonResponse({'success': False})


@csrf_exempt
def my_tasks_operator_scrap_task(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        scrap_product_num = int(request.POST.get('product_num_3'))

        try:
            # Get the OrderProduct instance
            task = Task.objects.get(id=task_id)
            task.product_num -= scrap_product_num
            task.completed = 0
            task.inspected = 0
            order_code = task.order_code
            order = get_object_or_404(Order, order_code=order_code)

            OrderProduct.objects.create(
                order=order,
                product_code=task.product_code+"_"+datetime.now().strftime("%Y-%m-%d %H:%M"),
                defaults={
                    'product_num_todo': scrap_product_num,
                }
            )

            task.save()

            product_code = task.product_code
            order_product = OrderProduct.objects.get(product_code=product_code,
                                                     order=order)

            # Set cur_process_i to 0
            order_product.cur_process_i = 0
            order_product.save()

            return JsonResponse({'success': True})
        except OrderProduct.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'OrderProduct not found'})

    return JsonResponse({'success': False})


def my_tasks_inspector_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'home/my_tasks_inspector_detail.html', {'task': task})


@csrf_exempt
def my_tasks_inspector_complete_task(request):
    if request.method == 'POST':
        # Update OrderProduct
        task_id = request.POST.get('task_id')
        num_inspected = int(request.POST.get('product_num'))
        task = Task.objects.get(id=task_id)
        task.product_num_inspected += num_inspected
        if task.product_num_inspected >= task.product_num:
            task.inspected = 1
        task.save()

        return JsonResponse({'success': True,
                             'product_num': task.product_num, })
    return JsonResponse({'success': False})


def generate_pdf(request):
    # 注册字体
    font_path = 'apps/static/assets/fonts/SourceHanSansCN-Medium.ttf'
    pdfmetrics.registerFont(TTFont('SourceHanSansCN', font_path))

    user = request.user
    if user.role == 'admin':
        tasks = Task.objects.all().order_by('task_start_time')
    elif user.role == 'inspector':
        related_device_names = Device.objects.filter(inspector=user).values_list('device_name', flat=True)
        tasks = Task.objects.filter(
            device_name__in=related_device_names,
            completed=1,
        ).order_by('task_start_time')
    else:
        related_device_names = Device.objects.filter(operator=user).values_list('device_name', flat=True)
        tasks = Task.objects.filter(device_name__in=related_device_names).order_by('task_start_time')

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # 使用 Source Han Sans CN 字体
    c.setFont("SourceHanSansCN", 13)
    c.drawString(x=50, y=height - 50, text=f"用户名:{user.username}\t角色:{user.role}")

    # 添加二维码图片
    qr_code_path = 'apps/static/assets/img/qrcode/my_tasks_qr.png'
    qr_code_width = 50  # 设置二维码图片宽度
    qr_code_height = 50  # 设置二维码图片高度
    qr_code_x = width - 30 - qr_code_width  # 图片X坐标
    qr_code_y = height - 30 - qr_code_height  # 图片Y坐标
    c.drawImage(qr_code_path, qr_code_x, qr_code_y, width=qr_code_width, height=qr_code_height)

    # 上海时区
    shanghai_tz = pytz.timezone('Asia/Shanghai')

    # 定义表格数据
    data = [['开始时间', '完成时间', '换型', '订单', '产品', '序号', '工序', '设备', '数量', '已完成',
             '已质检']]
    for task in tasks:
        start_time = task.task_start_time.astimezone(shanghai_tz)
        end_time = task.task_end_time.astimezone(shanghai_tz)
        data.append([
            start_time.strftime('%m-%d %H:%M'),
            end_time.strftime('%m-%d %H:%M'),
            task.is_changeover,
            task.order_code,
            task.product_code,
            task.process_i,
            task.process_name,
            task.device_name,
            task.product_num,
            task.product_num_completed,
            task.product_num_inspected
        ])

    # 设置表格位置
    table_x = 50
    # table_y = height - (len(tasks) + 1) * 35  # 增加间距，使表格不遮挡用户名
    table_y = 50
    table_width = width - 100  # 留出边距
    table_height = height - table_y - 50  # 留出底部边距
    print(table_x, table_y, table_width, table_height)

    table = Table(data, colWidths=[table_width / len(data[0])] * len(data[0]), rowHeights=0.4 * inch)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#d0e0f0'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'SourceHanSansCN'),  # 确保所有单元格都使用指定字体
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), '#f5f5f5'),
        ('GRID', (0, 0), (-1, -1), 1, '#d0d0d0'),
    ]))
    table.wrapOn(c, table_width, table_height)
    table.drawOn(c, table_x, table_y)

    # 不添加页脚
    # c.setFont("SourceHanSansCN", 10)
    # c.drawString(50, 40, "Page 1")

    c.showPage()
    c.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="production_task_list.pdf"'
    return response
