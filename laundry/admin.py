from django.contrib import admin
from .models import Customer, Order, Expense

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'location', 'total_orders', 'total_spent']
    search_fields = ['name', 'phone']
    list_filter = ['location']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'weight_kg', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'customer__name', 'customer__phone']
    readonly_fields = ['order_number', 'total_amount']  # These are auto-generated
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'items_description', 'weight_kg', 'price_per_kg', 'total_amount')
        }),
        ('Payment', {
            'fields': ('paid_amount', 'payment_status')
        }),
        ('Status', {
            'fields': ('status', 'pickup_date', 'notes')
        }),
    )

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'category', 'amount', 'date']
    list_filter = ['category', 'date']
