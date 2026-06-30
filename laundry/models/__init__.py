# laundry/models/__init__.py
from .models import (
    UserProfile,
    Customer,
    Order,
    Expense,
    Transaction,
    LedgerAccount,
)

from .accounting_models import (
    Account,
    BusinessContext,
    NaturalLanguageTransaction,
    Journal,
    JournalEntry,
    Document,
    AuditLog,
)

# Import Asset, Liability, Equity from accounting_models if they exist
try:
    from .accounting_models import Asset, Liability, Equity
except ImportError:
    from django.db import models
    
    class Asset(models.Model):
        name = models.CharField(max_length=200)
        asset_code = models.CharField(max_length=50)
        asset_type = models.CharField(max_length=50, default='fixed')
        purchase_date = models.DateField()
        purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
        current_value = models.DecimalField(max_digits=15, decimal_places=2)
        depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
        accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
        location = models.CharField(max_length=200, blank=True)
        description = models.TextField(blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        def __str__(self):
            return self.name
    
    class Liability(models.Model):
        name = models.CharField(max_length=200)
        liability_code = models.CharField(max_length=50)
        liability_type = models.CharField(max_length=50)
        amount = models.DecimalField(max_digits=15, decimal_places=2)
        interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
        due_date = models.DateField()
        creditor = models.CharField(max_length=200, blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        def __str__(self):
            return self.name
    
    class Equity(models.Model):
        name = models.CharField(max_length=200)
        equity_code = models.CharField(max_length=50)
        equity_type = models.CharField(max_length=50)
        amount = models.DecimalField(max_digits=15, decimal_places=2)
        owner = models.CharField(max_length=200, blank=True)
        description = models.TextField(blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        def __str__(self):
            return self.name

# Alias Account as LedgerAccount for backward compatibility
# Already imported above

__all__ = [
    'UserProfile', 'Customer', 'Order', 'Expense', 'Transaction',
    'Account', 'LedgerAccount', 'BusinessContext',
    'NaturalLanguageTransaction', 'Journal', 'JournalEntry',
    'Document', 'AuditLog', 'Asset', 'Liability', 'Equity'
]
