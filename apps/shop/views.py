from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, date, time, timedelta
from .models import Order, Purchase
from .forms import OrderForm
from utils.util_functions import parse_datetime, filter_items
import pytz


# datetime format
format_datetime = "%Y-%m-%d %H:%M:%S.%f"

def format_num(num, commas=False):
    formatted_num = int(num) if num == int(num) else num
    return '{:,.2f}'.format(formatted_num) if commas else formatted_num

# dashboard page
@never_cache
@login_required
def dashboard_page(request):
    def month_firstday(any_date):
        return any_date.replace(day=1)

    def month_lastday(any_date):
        next_month = any_date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
    
    def count_orders_purchases(startdate, enddate, item):
        if item == 'orders':
            get_orders = Order.objects.filter(Q(deleted=False), Q(regdate__range=(startdate, enddate)))
            return sum(item.price for item in get_orders)
        
        get_purchases = Purchase.objects.filter(Q(deleted=False), Q(regdate__range=(startdate, enddate)))
        return sum(item.cost+item.extra_cost for item in get_purchases)
    
    orders_qry = Order.objects.exclude(deleted=True)
    purchases_qry = Purchase.objects.exclude(deleted=True)
    today_date = date.today()
    start_of_week = today_date - timedelta(days=today_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    count_pending_orders = orders_qry.filter(status=False).count()
    count_credit_purchases = purchases_qry.filter(paid=False).count()
    count_week_due = orders_qry.filter(duedate__range=(start_of_week, end_of_week)).count()

    previous_days = [(today_date - timedelta(days=i)) for i in range(1, 5)]
    today_range = (datetime.combine(today_date, time.min), datetime.combine(today_date, time.max))
    previous_day_ranges = [
        (datetime.combine(day, time.min), datetime.combine(day, time.max)) for day in previous_days
    ]
    current_month_range = (
        datetime.combine(month_firstday(today_date), time.min), datetime.combine(month_lastday(today_date), time.max)
    )
    previous_months = [month_firstday(today_date.replace(day=1) - timedelta(days=i * 30)) for i in range(1, 5)]
    previous_month_ranges = [
        (
            datetime.combine(month_firstday(month), time.min), datetime.combine(month_lastday(month), time.max)
        ) for month in previous_months
    ]

    today_orders = count_orders_purchases(*today_range, 'orders')
    today_purchases = count_orders_purchases(*today_range, 'purchases')
    day_orders = [count_orders_purchases(*day_range, 'orders') for day_range in previous_day_ranges]
    day_purchases = [count_orders_purchases(*day_range, 'purchases') for day_range in previous_day_ranges]
    month_orders = count_orders_purchases(*current_month_range, 'orders')
    month_purchases = count_orders_purchases(*current_month_range, 'purchases')
    previous_month_orders = [count_orders_purchases(*month_range, 'orders') for month_range in previous_month_ranges]
    previous_month_purchases = [count_orders_purchases(*month_range, 'purchases') for month_range in previous_month_ranges]

    context = {
        'count_pending_orders': f"{count_pending_orders:,.0f}" if count_pending_orders > 9 else f"0{count_pending_orders}",
        'count_credit_purchases': f"{count_credit_purchases:,.0f}" if count_credit_purchases > 9 else f"0{count_credit_purchases}",
        'count_week_due': f"{count_week_due:,.0f}" if count_week_due > 9 else f"0{count_week_due}",
        'today_orders': f"{today_orders:,.2f} TZS",
        'today_purchases': f"{today_purchases:,.2f} TZS",
        'day1_orders': f"{day_orders[0]:,.2f} TZS",
        'day2_orders': f"{day_orders[1]:,.2f} TZS",
        'day3_orders': f"{day_orders[2]:,.2f} TZS",
        'day4_orders': f"{day_orders[3]:,.2f} TZS",
        'day1_purchases': f"{day_purchases[0]:,.2f} TZS",
        'day2_purchases': f"{day_purchases[1]:,.2f} TZS",
        'day3_purchases': f"{day_purchases[2]:,.2f} TZS",
        'day4_purchases': f"{day_purchases[3]:,.2f} TZS",
        'month_orders': f"{month_orders:,.2f} TZS",
        'month_purchases': f"{month_purchases:,.2f} TZS",
        'month1_orders': f"{previous_month_orders[0]:,.2f} TZS",
        'month2_orders': f"{previous_month_orders[1]:,.2f} TZS",
        'month3_orders': f"{previous_month_orders[2]:,.2f} TZS",
        'month4_orders': f"{previous_month_orders[3]:,.2f} TZS",
        'month1_purchases': f"{previous_month_purchases[0]:,.2f} TZS",
        'month2_purchases': f"{previous_month_purchases[1]:,.2f} TZS",
        'month3_purchases': f"{previous_month_purchases[2]:,.2f} TZS",
        'month4_purchases': f"{previous_month_purchases[3]:,.2f} TZS",
        'day2': previous_days[1].strftime('%d-%b-%Y'),
        'day3': previous_days[2].strftime('%d-%b-%Y'),
        'day4': previous_days[3].strftime('%d-%b-%Y'),
        'month2': previous_months[1].strftime('%b-%Y'),
        'month3': previous_months[2].strftime('%b-%Y'),
        'month4': previous_months[3].strftime('%b-%Y')
    }

    return render(request, 'shop/dashboard.html', context)

# orders page
@never_cache
@login_required
def orders_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Order.objects.exclude(deleted=True)

        # Date range filtering
        reg_start = parse_datetime(request.POST.get('start_reg'), format_datetime, to_utc=True)
        reg_end = parse_datetime(request.POST.get('end_reg'), format_datetime, to_utc=True)
        due_start = parse_datetime(request.POST.get('start_due'), format_datetime, to_date=True)
        due_end = parse_datetime(request.POST.get('end_due'), format_datetime, to_date=True)
        date_range_filters = Q()

        if reg_start and reg_end:
            date_range_filters |= Q(regdate__range=(reg_start, reg_end))
        else:
            if reg_start:
                date_range_filters |= Q(regdate__gte=reg_start)
            elif reg_end:
                date_range_filters |= Q(regdate__lte=reg_end)

        if due_start and due_end:
            date_range_filters |= Q(duedate__range=(due_start, due_end))
        else:
            if due_start:
                date_range_filters |= Q(duedate__gte=due_start)
            elif due_end:
                date_range_filters |= Q(duedate__lte=due_end)

        if date_range_filters:
            queryset = queryset.filter(date_range_filters)

        # Base data from queryset
        base_data, grand_total = [], 0.0
        for order in queryset:
            grand_total += order.price

            order_status = -1
            if order.status == True:
                order_status = 1
            elif order.status == False and order.duedate > date.today():
                order_status = 0

            order_object = {
                'id': order.id,
                'orderdate': order.regdate,
                'customer': order.customer,
                'phone': order.phone,
                'price': order.price,
                'duedate': order.duedate,
                'status': order_status,
                'user': order.user.username,
                'user_info': reverse('user_details', kwargs={'user_id': int(order.user.id)}),
                'user_type': 1 if request.user.is_admin and not order.user == request.user else 0,
                'order_info': reverse('order_details', kwargs={'order_id': int(order.id)})
            }
            base_data.append(order_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'orderdate',
            2: 'customer',
            3: 'phone',
            4: 'price',
            5: 'duedate',
            6: 'user',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'orderdate')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '').strip()
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    base_data = [item for item in base_data if filter_items(column_field, column_search, item, ('price'))]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Apply pagination
        if length < 0:
            length = len(base_data)
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'orderdate': item.get('orderdate').strftime('%d-%b-%Y %H:%M:%S'),
                'customer': item.get('customer'),
                'phone': item.get('phone'),
                'price': '{:,.2f}'.format(item.get('price'))+" TZS",
                'duedate': item.get('duedate').strftime('%d-%b-%Y'),
                'status': item.get('status'),
                'user': item.get('user'),
                'user_info': item.get('user_info'),
                'order_info': item.get('order_info'),
                'user_type': item.get('user_type'),
                'action': '',
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_total': grand_total,
        }
        return JsonResponse(ajax_response)
    return render(request, 'shop/orders.html')


# orders actions
@never_cache
@login_required
def orders_actions(request):
    if request.method == 'POST':
        try:
            edit_order = request.POST.get('edit_order')
            delete_order = request.POST.get('delete_order')
            complete_order = request.POST.get('complete_order')

            if delete_order:
                order_instance = Order.objects.get(id=delete_order)
                order_instance.deleted = True
                order_instance.save()
                return JsonResponse({'success': True, 'url': reverse('orders_page')})
            
            elif complete_order:
                order_instance = Order.objects.get(id=complete_order)
                order_instance.status = True
                order_instance.save()
                return JsonResponse({'success': True, 'sms': 'Order info updated successfully'})
            
            elif edit_order:
                order_instance = Order.objects.get(id=edit_order)
                form = OrderForm(request.POST, instance=order_instance)

                if form.is_valid():
                    prod = form.save(commit=False)
                    prod.comment = form.cleaned_data.get('description') or None
                    prod.save()

                    return JsonResponse({'success': True, 'update_success': True, 'sms': 'Order details updated successfully!'})
                else:
                    errorMsg = form.errors.get('customer', 'phone', ["Failed to update information"])[0]
                    return JsonResponse({'success': False, 'sms': errorMsg})
            
            else:
                form = OrderForm(request.POST)
                if form.is_valid():
                    prod = form.save(commit=False)
                    prod.user = request.user
                    prod.save()

                    return JsonResponse({'success': True, 'sms': 'New order recorded successfully!'})
                else:
                    # errorMsg = form.errors.get('names', 'phone', ["Failed to record new order."])[0]
                    errorMsg = form.errors.get('names') or form.errors.get('phone') or ["Failed to record new order."][0]
                    return JsonResponse({'success': False, 'sms': errorMsg})

        except Exception as e:
            return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})
        
    return JsonResponse({'success': False, 'sms': 'Invalid data'})

# product details
@never_cache
@login_required
def order_details(request, order_id):
    order_instance = Order.objects.filter(id=order_id, deleted=False).first()
    if request.method == 'GET' and order_instance:
        order_status = -1
        if order_instance.status == True:
            order_status = 1
        elif order_instance.status == False and order_instance.duedate > date.today():
            order_status = 0
        order_info = {
            'id': order_instance.id,
            'orderdate': order_instance.regdate.strftime('%d-%b-%Y %H:%M:%S'),
            'user': f'{order_instance.user.fullname} ({order_instance.user.username})',
            'customer': order_instance.customer,
            'phone': order_instance.phone,
            'duedate': order_instance.duedate.strftime('%d-%b-%Y'),
            'due_date': order_instance.duedate,
            'due_status': 1 if order_instance.duedate <= date.today() else 0,
            'price': '{:,.2f}'.format(format_num(order_instance.price))+" TZS",
            'cake_price': format_num(order_instance.price),
            'details': order_instance.description or '',
            'status': order_status,
            'user_type': 1 if request.user.is_admin and not order_instance.user == request.user else 0,
            'user_info': reverse('user_details', kwargs={'user_id': int(order_instance.user.id)})
        }
        return render(request, 'shop/orders.html', {'order': order_info})
    return redirect('orders_page')

# purchases page
@never_cache
@login_required
def purchases_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Purchase.objects.exclude(deleted=True)

        # Date range filtering
        reg_start = parse_datetime(request.POST.get('start_reg'), format_datetime, to_utc=True)
        reg_end = parse_datetime(request.POST.get('end_reg'), format_datetime, to_utc=True)
        purchase_start = parse_datetime(request.POST.get('purchase_start'), format_datetime, to_date=True)
        purchase_end = parse_datetime(request.POST.get('purchase_end'), format_datetime, to_date=True)
        date_range_filters = Q()

        if reg_start and reg_end:
            date_range_filters |= Q(regdate__range=(reg_start, reg_end))
        else:
            if reg_start:
                date_range_filters |= Q(regdate__gte=reg_start)
            elif reg_end:
                date_range_filters |= Q(regdate__lte=reg_end)

        if purchase_start and purchase_end:
            date_range_filters |= Q(purchasedate__range=(purchase_start, purchase_end))
        else:
            if purchase_start:
                date_range_filters |= Q(purchasedate__gte=purchase_start)
            elif purchase_end:
                date_range_filters |= Q(purchasedate__lte=purchase_end)

        if date_range_filters:
            queryset = queryset.filter(date_range_filters)

        # Base data from queryset
        base_data, cost_total, extra_cost_total = [], 0.0, 0.0
        for item in queryset:
            cost_total += item.cost
            extra_cost_total += item.extra_cost

            paid_type = 'CASH'
            if item.payment == 'CRE' and item.paid:
                paid_type = 'CREDIT(Paid)'
            elif item.payment == 'CRE':
                paid_type = 'CREDIT'

            purchase_object = {
                'id': item.id,
                'recordDate': item.regdate,
                'purchaseDate': item.purchasedate,
                'itemName': item.product,
                'supplierName': item.supplier,
                'itemCost': item.cost,
                'extraCost': item.extra_cost,
                'payType': paid_type,
                'paidStatus': int(item.paid),
                'user': item.user.username,
                'userInfo': reverse('user_details', kwargs={'user_id': int(item.user.id)}),
                'userType': 1 if request.user.is_admin and not item.user == request.user else 0,
                'purchaseInfo': reverse('purchase_details', kwargs={'purchase_id': int(item.id)})
            }
            base_data.append(purchase_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'recordDate',
            2: 'purchaseDate',
            3: 'itemName',
            4: 'supplierName',
            5: 'itemCost',
            6: 'extraCost',
            7: 'payType',
            8: 'user',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'recordDate')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '').strip()
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    base_data = [item for item in base_data if filter_items(column_field, column_search, item, ('itemCost', 'extraCost'), ('payType'))]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Apply pagination
        if length < 0:
            length = len(base_data)
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'recordDate': item.get('recordDate').strftime('%d-%b-%Y %H:%M:%S'),
                'purchaseDate': item.get('purchaseDate').strftime('%d-%b-%Y'),
                'itemName': item.get('itemName'),
                'supplierName': item.get('supplierName'),
                'itemCost': '{:,.2f}'.format(item.get('itemCost'))+" TZS",
                'extraCost': '{:,.2f}'.format(item.get('extraCost'))+" TZS" if item.get('extraCost') > 0 else 'N/A',
                'payType': item.get('payType'),
                'paidStatus': item.get('paidStatus'),
                'user': item.get('user'),
                'userInfo': item.get('userInfo'),
                'userType': item.get('userType'),
                'purchaseInfo': item.get('purchaseInfo'),
                'action': '',
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'cost_total': cost_total,
            'extra_total': extra_cost_total,
        }
        return JsonResponse(ajax_response)
    return render(request, 'shop/purchases.html')


# orders actions
@never_cache
@login_required
def purchases_actions(request):
    if request.method == 'POST':
        try:
            edit_purchase = request.POST.get('edit_purchase')
            delete_purchase = request.POST.get('delete_purchase')
            pay_purchases = request.POST.get('pay_purchase')

            if delete_purchase:
                purchase_instance = Purchase.objects.get(id=delete_purchase)
                purchase_instance.deleted = True
                purchase_instance.save()
                return JsonResponse({'success': True, 'url': reverse('purchases_page')})
            
            elif pay_purchases:
                purchase_instance = Purchase.objects.get(id=pay_purchases)
                purchase_instance.paid = True
                purchase_instance.save()
                return JsonResponse({'success': True, 'sms': 'Purchases info updated successfully'})
            
            elif edit_purchase:
                purchase_instance = Purchase.objects.get(id=edit_purchase)

                itemName = request.POST.get('product').strip()
                if len(itemName) < 3:
                    return JsonResponse({'success': False, 'sms': "Item name is too short."})
                
                supplierName = request.POST.get('supplier').strip()
                if len(supplierName) < 3:
                    return JsonResponse({'success': False, 'sms': "Supplier name is too short."})
                
                extraCost = request.POST.get('extra_cost')
                description = None if request.POST.get('description').strip() == "" else request.POST.get('description').strip()
                
                purchase_instance.purchasedate = request.POST.get('purchasedate')
                purchase_instance.product = itemName
                purchase_instance.supplier = supplierName
                purchase_instance.payment = request.POST.get('payment')
                purchase_instance.paid = purchase_instance.paid if request.POST.get('payment') == 'CRE' else True
                purchase_instance.cost = request.POST.get('cost')
                purchase_instance.extra_cost = 0.0 if extraCost == "" else extraCost
                purchase_instance.description = description
                purchase_instance.user = request.user
                purchase_instance.save()
                
                return JsonResponse({'success': True, 'update_success': True, 'sms': 'Purchase details updated successfully!'})
            
            else:
                itemName = request.POST.get('product').strip()
                if len(itemName) < 3:
                    return JsonResponse({'success': False, 'sms': "Item name is too short."})
                
                supplierName = request.POST.get('supplier').strip()
                if len(supplierName) < 3:
                    return JsonResponse({'success': False, 'sms': "Supplier name is too short."})
                
                extraCost = request.POST.get('extra_cost')
                description = None if request.POST.get('description').strip() == "" else request.POST.get('description').strip()
                
                Purchase.objects.create(
                    purchasedate = request.POST.get('purchasedate'),
                    product = itemName,
                    supplier = supplierName,
                    payment = request.POST.get('payment'),
                    paid = False if request.POST.get('payment') == 'CRE' else True,
                    cost = request.POST.get('cost'),
                    extra_cost = 0.0 if extraCost == "" else extraCost,
                    description = description,
                    user = request.user
                )
                
                return JsonResponse({'success': True, 'sms': 'New purchase recorded successfully!'})

        except Exception as e:
            return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})
        
    return JsonResponse({'success': False, 'sms': 'Invalid data'})

# product details
@never_cache
@login_required
def purchase_details(request, purchase_id):
    obj = Purchase.objects.filter(id=purchase_id, deleted=False).first()
    if request.method == 'GET' and obj:
        paid_type = 'CASH'
        if obj.payment == 'CRE' and obj.paid:
            paid_type = 'CREDIT(Paid)'
        elif obj.payment == 'CRE':
            paid_type = 'CREDIT'

        purchase_info = {
            'id': obj.id,
            'recordDate': obj.regdate.strftime('%d-%b-%Y %H:%M:%S'),
            'purchaseDate': obj.purchasedate.strftime('%d-%b-%Y'),
            'date_purchase': obj.purchasedate,
            'itemName': obj.product,
            'supplierName': obj.supplier,
            'paymentType': paid_type,
            'paidStatus': int(obj.paid),
            'itemCost': '{:,.2f}'.format(format_num(obj.cost))+" TZS",
            'extraCost': 'N/A' if obj.extra_cost == 0.0 else '{:,.2f}'.format(format_num(obj.extra_cost))+" TZS",
            'cost': obj.cost,
            'cost_extra': obj.extra_cost,
            'user': f'{obj.user.fullname} ({obj.user.username})',
            'details': obj.description or '',
            'userType': 1 if request.user.is_admin and not obj.user == request.user else 0,
            'userInfo': reverse('user_details', kwargs={'user_id': int(obj.user.id)})
        }
        return render(request, 'shop/purchases.html', {'purchase': purchase_info})
    return redirect('purchases_page')
