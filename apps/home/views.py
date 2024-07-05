# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import logging
import os

from django import template
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import Order, OrderProduct
from .models import Process, Raw, ExchangeTypeTime, Product
from .preprocess import preprocess_order, preprocess_product, preprocess_process, preprocess_exchange, preprocess_raw

logger = logging.getLogger(__name__)


@login_required(login_url="/login/")
def index(request):
    orders_count = Order.objects.count()
    products_count = Product.objects.count()
    raw_count = Raw.objects.count()
    exchange_count = ExchangeTypeTime.objects.count()
    process_count = Process.objects.count()
    context = {
        'segment': 'index',
        'orders_count': orders_count,
        'products_count': products_count,
        'raw_count': raw_count,
        'exchange_count': exchange_count,
        'process_count': process_count
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
                preprocess_exchange(file_path)
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
                preprocess_exchange(file_path)
            else:
                raise ValueError("Invalid file type.")

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(str(e), exc_info=True)  # 记录详细的错误信息
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def order_list(request):
    sort_by = request.GET.get('sort_by', 'order_date')  # 默认按 order_id 排序
    orders = Order.objects.all().order_by(sort_by)
    return render(request, 'home/order_list.html', {'orders': orders})


def order_product_list(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    products = OrderProduct.objects.filter(order=order)
    context = {
        'order': order,
        'products': products
    }
    return render(request, 'home/order_product_list.html', context)


def get_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    data = {
        'order_id': order.order_id,
        'order_date': order.order_date,
        'customer': order.customer,
        'sale_amount': order.sale_amount,
        'order_state': order.order_state,
    }
    return JsonResponse(data)


def update_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id)
        order.order_date = request.POST.get('order_date')
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


def exchange_list(request):
    exchanges = ExchangeTypeTime.objects.all()
    return render(request, 'home/exchange_list.html', {'exchanges': exchanges})


def get_exchange(request, exchange_id):
    exchange = get_object_or_404(ExchangeTypeTime, id=exchange_id)
    data = {
        'device_name': exchange.device_name,
        'exchange_time': exchange.exchange_time,
        'current_raw': exchange.current_raw,
    }
    return JsonResponse(data)


def update_exchange(request, exchange_id):
    if request.method == 'POST':
        exchange = get_object_or_404(ExchangeTypeTime, id=exchange_id)
        exchange.device_name = request.POST.get('device_name')
        exchange.exchange_time = request.POST.get('exchange_time')
        exchange.current_raw = request.POST.get('current_raw')
        exchange.save()
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def delete_exchange(request, exchange_id):
    if request.method == 'POST':
        exchange = get_object_or_404(ExchangeTypeTime, id=exchange_id)
        exchange.delete()
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
        raw_code = product.raw.raw_code if product.raw else ''
        product_list.append({
            'id': product.id,
            'product_code': product.product_code,
            'product_category': product.product_category,
            'raw_code': raw_code
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
        'raw': product.raw.raw_code if product.raw else None,
    }
    return JsonResponse(data)


def update_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.product_code = request.POST.get('product_code')
        product.product_category = request.POST.get('product_category')
        raw_code = request.POST.get('raw')
        if raw_code:
            product.raw = get_object_or_404(Raw, raw_code=raw_code)
        else:
            product.raw = None
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
