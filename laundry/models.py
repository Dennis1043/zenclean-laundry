from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True, help_text="Primary location/area for deliveries")
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('washing', 'Washing'),
        ('drying', 'Drying'),
        ('folding', 'Folding'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    items_description = models.TextField(blank=True, help_text="e.g., 5 bedsheets, 3 jackets, 2 jeans")
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2, default=100.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='unpaid')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    notes = models.TextField(blank=True)
    pickup_date = models.DateField(null=True, blank=True, help_text="Date when customer will pick up")
    collection_date = models.DateField(null=True, blank=True, help_text="Date when clothes are ready for collection")
    sms_sent = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-calculate total amount
        if self.weight_kg and self.price_per_kg:
            self.total_amount = self.weight_kg * self.price_per_kg
        
        # Auto-generate order number if not provided
        if not self.order_number:
            today = timezone.now().strftime('%y%m%d')
            today_orders = Order.objects.filter(created_at__date=timezone.now().date()).count()
            self.order_number = f"ZC-{today}-{str(today_orders + 1).zfill(4)}"
        
        # Auto-update payment status based on paid amount
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_balance(self):
        if self.total_amount and self.paid_amount:
            return self.total_amount - self.paid_amount
        return self.total_amount or 0
    
    @property
    def is_fully_paid(self):
        return self.payment_status == 'paid'
    
    def update_payment_status(self):
        """Auto-update payment status based on paid amount"""
        if self.total_amount and self.paid_amount >= self.total_amount:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
    
    def __str__(self):
        return f"#{self.order_number} - {self.customer.name}"

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('detergent', 'Detergent'),
        ('water', 'Water'),
        ('electricity', 'Electricity'),
        ('maintenance', 'Maintenance'),
        ('salary', 'Salary'),
        ('rent', 'Rent'),
        ('other', 'Other'),
    ]
    
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.category} - {self.amount} on {self.date}"