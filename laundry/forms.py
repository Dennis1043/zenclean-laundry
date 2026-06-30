from django import forms
from .models import Customer, Order, Expense

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'location', 'apartment_name', 'floor', 'door_number']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'items_description', 'weight_kg', 'price_per_kg', 'status', 'payment_status', 'paid_amount', 'notes']

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'category', 'amount', 'date', 'notes']
