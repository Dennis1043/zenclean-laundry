# laundry/models/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, default='staff')
    is_manager = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=200, blank=True)
    apartment_name = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=20, blank=True)
    door_number = models.CharField(max_length=20, blank=True)
    total_orders = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.phone}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('washing', 'Washing'),
        ('drying', 'Drying'),
        ('folding', 'Folding'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    items_description = models.TextField(blank=True)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='unpaid')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            from datetime import datetime
            self.order_number = f"ZC-{datetime.now().strftime('%y%m%d')}-{Order.objects.count() + 1:04d}"
        self.total_amount = self.weight_kg * self.price_per_kg
        super().save(*args, **kwargs)
    
    @property
    def remaining_balance(self):
        return self.total_amount - self.paid_amount

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('rent', 'Rent'),
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('detergent', 'Detergent'),
        ('maintenance', 'Maintenance'),
        ('asset_purchase', 'Asset Purchase'),
        ('other', 'Other'),
    ]
    
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW: link to the journal created for this expense
    journal = models.ForeignKey('Journal', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.description} - {self.amount}"

class Transaction(models.Model):
    """Transaction model for smart transactions"""
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=50, default='expense')
    detected_category = models.CharField(max_length=50, blank=True)
    detected_subcategory = models.CharField(max_length=50, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    analyzed_data = models.JSONField(default=dict, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transactions')
    verified_at = models.DateTimeField(null=True, blank=True)
    detected_account = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, blank=True)
    related_journal = models.ForeignKey('Journal', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description} - {self.amount}"

# Alias for backward compatibility
from .accounting_models import Account as LedgerAccount

__all__ = [
    'UserProfile', 'Customer', 'Order', 'Expense', 'Transaction', 'LedgerAccount'
]
