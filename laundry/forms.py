from django import forms
from .models import Order, Customer, Expense

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'items_description', 'weight_kg', 'price_per_kg', 'status', 'payment_status', 'paid_amount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'items_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g., 5 bedsheets, 3 jackets'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'id': 'id_weight_kg'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'id': 'id_price_per_kg'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order customers by name
        self.fields['customer'].queryset = Customer.objects.all().order_by('name')
        # Add empty label
        self.fields['customer'].empty_label = "Select a customer"

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Westlands, CBD'}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'category', 'amount', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'required': 'required'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
