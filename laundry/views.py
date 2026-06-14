from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
import json
from .models import Order, Customer, Expense
from .forms import OrderForm, CustomerForm, ExpenseForm

# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Greeting
    hour = timezone.now().hour
    if hour < 12:
        greeting = "morning"
    elif hour < 17:
        greeting = "afternoon"
    else:
        greeting = "evening"
    
    # Order Status Counts
    received_orders = Order.objects.filter(status='received').count()
    washing_orders = Order.objects.filter(status='washing').count()
    drying_orders = Order.objects.filter(status='drying').count()
    folding_orders = Order.objects.filter(status='folding').count()
    ready_orders = Order.objects.filter(status='ready').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    # Progress orders
    progress_orders = washing_orders + drying_orders + folding_orders
    
    # Payment Status Counts
    paid_orders = Order.objects.filter(payment_status='paid')
    unpaid_orders = Order.objects.filter(payment_status='unpaid')
    partial_orders = Order.objects.filter(payment_status='partial')
    
    paid_count = paid_orders.count()
    unpaid_count = unpaid_orders.count()
    partial_count = partial_orders.count()
    
    # Revenue
    total_revenue = paid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_revenue = unpaid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_orders_count = unpaid_orders.count() + partial_orders.count()
    
    # Today's stats
    today_orders = Order.objects.filter(created_at__date=today)
    today_paid_orders = today_orders.filter(payment_status='paid')
    today_revenue = today_paid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    today_expenses = Expense.objects.filter(date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Weekly stats
    weekly_orders = Order.objects.filter(created_at__date__gte=week_ago)
    weekly_orders_count = weekly_orders.count()
    weekly_paid_orders = weekly_orders.filter(payment_status='paid')
    weekly_revenue = weekly_paid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Chart data
    week_data = []
    week_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_orders = Order.objects.filter(created_at__date=day, payment_status='paid')
        revenue = day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        week_data.append(float(revenue))
        week_labels.append(day.strftime('%a'))
    
    # Weekly percentage
    last_week_start = week_ago - timedelta(days=7)
    last_week_orders = Order.objects.filter(
        created_at__date__gte=last_week_start,
        created_at__date__lt=week_ago,
        payment_status='paid'
    )
    last_week_revenue = last_week_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    if last_week_revenue > 0:
        weekly_percentage = round((weekly_revenue - last_week_revenue) / last_week_revenue * 100)
    else:
        weekly_percentage = 100 if weekly_revenue > 0 else 0
    
    # New customers
    month_ago = today - timedelta(days=30)
    new_customers = Customer.objects.filter(created_at__date__gte=month_ago).count()
    
    # Completion rate
    total_orders_count = Order.objects.count()
    if total_orders_count > 0:
        completion_rate = round((completed_orders / total_orders_count) * 100)
    else:
        completion_rate = 0
    
    # Lists
    ready_orders_list = Order.objects.filter(status='ready').order_by('-created_at')[:10]
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    total_customers = Customer.objects.count()
    
    context = {
        'greeting': greeting,
        'received_orders': received_orders,
        'washing_orders': washing_orders,
        'drying_orders': drying_orders,
        'folding_orders': folding_orders,
        'progress_orders': progress_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'partial_count': partial_count,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'pending_orders_count': pending_orders_count,
        'today_orders': today_orders.count(),
        'today_revenue': today_revenue,
        'today_expenses': today_expenses,
        'today_profit': today_revenue - today_expenses,
        'weekly_orders': weekly_orders_count,
        'weekly_revenue': weekly_revenue,
        'weekly_percentage': weekly_percentage,
        'week_data': week_data,
        'week_labels': week_labels,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'completion_rate': completion_rate,
        'ready_orders_list': ready_orders_list,
        'recent_orders': recent_orders,
    }
    return render(request, 'laundry/dashboard.html', context)


# ==================== ORDERS ====================
@login_required
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'laundry/orders.html', {'orders': orders})


@login_required
def order_create(request):
    if request.method == 'POST':
        phone = request.POST.get('customer_phone')
        name = request.POST.get('customer_name')
        location = request.POST.get('customer_location', '')
        existing_customer_id = request.POST.get('existing_customer_id')
        
        if existing_customer_id:
            customer = get_object_or_404(Customer, id=existing_customer_id)
        else:
            customer = Customer.objects.create(
                name=name,
                phone=phone,
                location=location
            )
        
        try:
            weight_kg = float(request.POST.get('weight_kg', 0))
            price_per_kg = float(request.POST.get('price_per_kg', 100))
            paid_amount = float(request.POST.get('paid_amount', 0))
        except ValueError:
            weight_kg = 0
            price_per_kg = 100
            paid_amount = 0
        
        order = Order(
            customer=customer,
            items_description=request.POST.get('items_description', ''),
            weight_kg=weight_kg,
            price_per_kg=price_per_kg,
            status=request.POST.get('status', 'received'),
            payment_status=request.POST.get('payment_status', 'unpaid'),
            paid_amount=paid_amount,
            notes=request.POST.get('notes', ''),
            created_by=request.user
        )
        order.save()
        return redirect('order_list')
    
    return render(request, 'laundry/order_form.html', {'title': 'New Order'})


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)
    return render(request, 'laundry/order_form.html', {'form': form, 'title': 'Edit Order'})


@login_required
def update_order_status(request, order_id, status):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, id=order_id)
            order.status = status
            order.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def update_order_payment(request, order_id, payment_status):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, id=order_id)
            order.payment_status = payment_status
            if payment_status == 'paid':
                order.paid_amount = order.total_amount
            order.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def mark_all_ready_completed(request):
    if request.method == 'POST':
        try:
            count = Order.objects.filter(status='ready').update(status='completed')
            return JsonResponse({'success': True, 'message': f'{count} order(s) marked as completed!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


# ==================== CUSTOMERS ====================
@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-total_orders')
    return render(request, 'laundry/customers.html', {'customers': customers})


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'laundry/customer_form.html', {'form': form, 'title': 'New Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'laundry/customer_form.html', {'form': form, 'title': 'Edit Customer'})


@login_required
def find_customer_by_phone(request, phone):
    try:
        customer = Customer.objects.get(phone=phone)
        return JsonResponse({
            'exists': True,
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'location': customer.location or ''
        })
    except Customer.DoesNotExist:
        return JsonResponse({'exists': False})


# ==================== EXPENSES ====================
@login_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'laundry/expenses.html', {'expenses': expenses, 'total_expenses': total_expenses})


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'laundry/expense_form.html', {'form': form, 'title': 'New Expense'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'laundry/expense_form.html', {'form': form, 'title': 'Edit Expense'})


# ==================== REPORTS & RECEIPTS ====================
@login_required
def reports(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    total_orders_count = Order.objects.count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_customers = Customer.objects.count()
    
    weekly_revenue = Order.objects.filter(created_at__date__gte=week_ago, payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    monthly_revenue = Order.objects.filter(created_at__date__gte=month_ago, payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    daily_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        revenue = Order.objects.filter(created_at__date=day, payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        expenses = Expense.objects.filter(date=day).aggregate(Sum('amount'))['amount__sum'] or 0
        daily_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'revenue': float(revenue),
            'expenses': float(expenses),
            'profit': float(revenue - expenses)
        })
    
    context = {
        'total_orders': total_orders_count,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'total_profit': total_revenue - total_expenses,
        'total_customers': total_customers,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'daily_data': daily_data,
    }
    return render(request, 'laundry/reports.html', context)


@login_required
def receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'laundry/receipt.html', {'order': order})


# ==================== AUTH ====================
@login_required
def logout_view(request):
    logout(request)
    return redirect('/admin/login/')