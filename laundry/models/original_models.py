from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    apartment_name = models.CharField(max_length=200, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    door_number = models.CharField(max_length=50, blank=True)
    total_orders = models.IntegerField(default=0)
    total_spent = models.IntegerField(default=0)
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
    items_description = models.TextField(blank=True)
    weight_kg = models.IntegerField(default=0)
    price_per_kg = models.IntegerField(default=100)
    total_amount = models.IntegerField(default=0)
    paid_amount = models.IntegerField(default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='unpaid')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    notes = models.TextField(blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    collection_date = models.DateField(null=True, blank=True)
    sms_sent = models.BooleanField(default=False)
    sms_order_received_sent = models.BooleanField(default=False)
    sms_ready_sent = models.BooleanField(default=False)
    sms_payment_sent = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.weight_kg and self.price_per_kg:
            self.total_amount = self.weight_kg * self.price_per_kg
        
        if not self.order_number:
            today = timezone.now().strftime('%y%m%d')
            today_orders = Order.objects.filter(created_at__date=timezone.now().date()).count()
            self.order_number = f"ZC-{today}-{str(today_orders + 1).zfill(4)}"
        
        self.update_payment_status()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # CRITICAL: Create accounting entries for new orders
        if is_new and self.total_amount > 0:
            self._create_accounting_entries()
    
    @property
    def remaining_balance(self):
        if self.total_amount and self.paid_amount:
            return self.total_amount - self.paid_amount
        return self.total_amount or 0
    
    @property
    def is_fully_paid(self):
        return self.payment_status == 'paid'
    
    def update_payment_status(self):
        if self.total_amount and self.paid_amount >= self.total_amount:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
    
    def _create_accounting_entries(self):
        from .models import Journal, JournalEntry, LedgerAccount
        
        try:
            revenue_account, _ = LedgerAccount.objects.get_or_create(
                account_code='4000',
                defaults={
                    'name': 'Laundry Service Revenue',
                    'account_type': 'revenue',
                    'normal_balance': 'C',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            cash_account, _ = LedgerAccount.objects.get_or_create(
                account_code='1000',
                defaults={
                    'name': 'Cash',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            accounts_receivable, _ = LedgerAccount.objects.get_or_create(
                account_code='1200',
                defaults={
                    'name': 'Accounts Receivable',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            journal = Journal.objects.create(
                entry_number=f"ORD-{self.order_number}",
                journal_type='sales',
                date=timezone.now().date(),
                description=f"Order #{self.order_number} - {self.customer.name}",
                reference=self.order_number,
                total_amount=self.total_amount,
                created_by=self.created_by
            )
            
            if self.payment_status == 'paid':
                JournalEntry.objects.create(
                    journal=journal,
                    account=cash_account,
                    debit=self.total_amount,
                    credit=0,
                    description=f"Cash payment for order #{self.order_number}",
                    order=self
                )
                JournalEntry.objects.create(
                    journal=journal,
                    account=revenue_account,
                    debit=0,
                    credit=self.total_amount,
                    description=f"Revenue from order #{self.order_number}",
                    order=self
                )
            else:
                JournalEntry.objects.create(
                    journal=journal,
                    account=accounts_receivable,
                    debit=self.total_amount,
                    credit=0,
                    description=f"Credit sale - order #{self.order_number}",
                    order=self
                )
                JournalEntry.objects.create(
                    journal=journal,
                    account=revenue_account,
                    debit=0,
                    credit=self.total_amount,
                    description=f"Revenue from order #{self.order_number}",
                    order=self
                )
            
            self._update_account_balances()
            
        except Exception as e:
            print(f"Error creating accounting entries: {e}")
    
    def _create_payment_entries(self):
        from .models import Journal, JournalEntry, LedgerAccount
        
        try:
            cash_account, _ = LedgerAccount.objects.get_or_create(
                account_code='1000',
                defaults={
                    'name': 'Cash',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            accounts_receivable, _ = LedgerAccount.objects.get_or_create(
                account_code='1200',
                defaults={
                    'name': 'Accounts Receivable',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            journal = Journal.objects.create(
                entry_number=f"PAY-{self.order_number}-{timezone.now().strftime('%Y%m%d')}",
                journal_type='cash_receipts',
                date=timezone.now().date(),
                description=f"Payment received for order #{self.order_number}",
                reference=self.order_number,
                total_amount=self.paid_amount,
                created_by=self.created_by
            )
            
            JournalEntry.objects.create(
                journal=journal,
                account=cash_account,
                debit=self.paid_amount,
                credit=0,
                description=f"Cash received for order #{self.order_number}",
                order=self
            )
            JournalEntry.objects.create(
                journal=journal,
                account=accounts_receivable,
                debit=0,
                credit=self.paid_amount,
                description=f"Payment received - reducing receivable",
                order=self
            )
            
            self._update_account_balances()
            
        except Exception as e:
            print(f"Error creating payment entries: {e}")
    
    def _update_account_balances(self):
        from .models import LedgerAccount, JournalEntry
        from django.db.models import Sum
        
        for account in LedgerAccount.objects.filter(is_active=True):
            total_debit = JournalEntry.objects.filter(account=account).aggregate(Sum('debit'))['debit__sum'] or 0
            total_credit = JournalEntry.objects.filter(account=account).aggregate(Sum('credit'))['credit__sum'] or 0
            
            if account.normal_balance == 'D':
                account.current_balance = account.opening_balance + total_debit - total_credit
            else:
                account.current_balance = account.opening_balance + total_credit - total_debit
            account.save()
    
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
        ('asset_purchase', 'Asset Purchase'),
        ('other', 'Other'),
    ]
    
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # CRITICAL: Create accounting entries for new expenses
        if is_new and self.amount > 0:
            self._create_accounting_entries()
        elif not is_new and self.amount > 0:
            self.update_accounting_entries()
    
    def _create_accounting_entries(self):
        from .models import Journal, JournalEntry, LedgerAccount, Asset
        
        try:
            if self.category == 'asset_purchase':
                self._handle_asset_purchase()
                return
            
            account_code = self._get_expense_account_code()
            account_name = self.category.capitalize() + ' Expense'
            
            expense_account, _ = LedgerAccount.objects.get_or_create(
                account_code=account_code,
                defaults={
                    'name': account_name,
                    'account_type': 'expense',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            cash_account, _ = LedgerAccount.objects.get_or_create(
                account_code='1000',
                defaults={
                    'name': 'Cash',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            journal = Journal.objects.create(
                entry_number=f"EXP-{self.id}-{timezone.now().strftime('%Y%m%d')}",
                journal_type='cash_payments',
                date=timezone.now().date(),
                description=f"Expense: {self.description}",
                reference=str(self.id),
                total_amount=self.amount,
                created_by=self.created_by
            )
            
            JournalEntry.objects.create(
                journal=journal,
                account=expense_account,
                debit=self.amount,
                credit=0,
                description=f"{self.category} expense",
                expense=self
            )
            JournalEntry.objects.create(
                journal=journal,
                account=cash_account,
                debit=0,
                credit=self.amount,
                description=f"Payment for {self.description}",
                expense=self
            )
            
            self._update_account_balances()
            
        except Exception as e:
            print(f"Error creating expense entries: {e}")
    
    def _handle_asset_purchase(self):
        from .models import Journal, JournalEntry, LedgerAccount, Asset
        
        try:
            asset_name = self.description.replace('Purchased', '').strip()
            asset = Asset.objects.create(
                asset_code=f"ASSET-{Asset.objects.count() + 1:04d}",
                name=asset_name or 'New Asset',
                asset_type='fixed',
                purchase_date=self.date,
                purchase_price=self.amount,
                current_value=self.amount,
                depreciation_rate=10,
                accumulated_depreciation=0,
                location='Main Store',
                description=self.description
            )
            
            asset_account, _ = LedgerAccount.objects.get_or_create(
                account_code='1400',
                defaults={
                    'name': 'Fixed Assets',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            cash_account, _ = LedgerAccount.objects.get_or_create(
                account_code='1000',
                defaults={
                    'name': 'Cash',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            journal = Journal.objects.create(
                entry_number=f"ASST-{asset.id}-{timezone.now().strftime('%Y%m%d')}",
                journal_type='purchases',
                date=timezone.now().date(),
                description=f"Asset Purchase: {self.description}",
                reference=str(asset.id),
                total_amount=self.amount,
                created_by=self.created_by
            )
            
            JournalEntry.objects.create(
                journal=journal,
                account=asset_account,
                debit=self.amount,
                credit=0,
                description=f"Purchase of {asset_name}",
                expense=self
            )
            JournalEntry.objects.create(
                journal=journal,
                account=cash_account,
                debit=0,
                credit=self.amount,
                description=f"Payment for {asset_name}",
                expense=self
            )
            
            self._update_account_balances()
            
        except Exception as e:
            print(f"Error handling asset purchase: {e}")
    
    def update_accounting_entries(self):
        from .models import Journal, JournalEntry, LedgerAccount
        
        try:
            JournalEntry.objects.filter(expense=self).delete()
            
            if self.category == 'asset_purchase':
                self._handle_asset_purchase()
                return
            
            account_code = self._get_expense_account_code()
            account_name = self.category.capitalize() + ' Expense'
            
            expense_account, _ = LedgerAccount.objects.get_or_create(
                account_code=account_code,
                defaults={
                    'name': account_name,
                    'account_type': 'expense',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            cash_account, _ = LedgerAccount.objects.get_or_create(
                account_code='1000',
                defaults={
                    'name': 'Cash',
                    'account_type': 'asset',
                    'normal_balance': 'D',
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            
            journal = Journal.objects.filter(
                reference=str(self.id),
                journal_type='cash_payments'
            ).first()
            
            if not journal:
                journal = Journal.objects.create(
                    entry_number=f"EXP-{self.id}-{timezone.now().strftime('%Y%m%d')}",
                    journal_type='cash_payments',
                    date=timezone.now().date(),
                    description=f"Expense: {self.description}",
                    reference=str(self.id),
                    total_amount=self.amount,
                    created_by=self.created_by
                )
            else:
                journal.total_amount = self.amount
                journal.description = f"Expense: {self.description}"
                journal.save()
            
            JournalEntry.objects.create(
                journal=journal,
                account=expense_account,
                debit=self.amount,
                credit=0,
                description=f"{self.category} expense",
                expense=self
            )
            JournalEntry.objects.create(
                journal=journal,
                account=cash_account,
                debit=0,
                credit=self.amount,
                description=f"Payment for {self.description}",
                expense=self
            )
            
            self._update_account_balances()
            
        except Exception as e:
            print(f"Error updating accounting entries for expense {self.id}: {e}")
    
    def _get_expense_account_code(self):
        codes = {
            'detergent': '5300',
            'water': '5400',
            'electricity': '5500',
            'maintenance': '5600',
            'salary': '5000',
            'rent': '5100',
            'other': '5900',
            'asset_purchase': '1400',
        }
        return codes.get(self.category, '5900')
    
    def _update_account_balances(self):
        from .models import LedgerAccount, JournalEntry
        from django.db.models import Sum
        
        for account in LedgerAccount.objects.filter(is_active=True):
            total_debit = JournalEntry.objects.filter(account=account).aggregate(Sum('debit'))['debit__sum'] or 0
            total_credit = JournalEntry.objects.filter(account=account).aggregate(Sum('credit'))['credit__sum'] or 0
            
            if account.normal_balance == 'D':
                account.current_balance = account.opening_balance + total_debit - total_credit
            else:
                account.current_balance = account.opening_balance + total_credit - total_debit
            account.save()
    
    def __str__(self):
        return f"{self.category} - {self.amount} on {self.date}"


# ==================== ACCOUNTING MODELS ====================

class LedgerAccount(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    
    account_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    description = models.TextField(blank=True)
    normal_balance = models.CharField(max_length=1, choices=[('D', 'Debit'), ('C', 'Credit')])
    opening_balance = models.IntegerField(default=0)
    current_balance = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account_code} - {self.name}"

class Journal(models.Model):
    JOURNAL_TYPES = [
        ('general', 'General Journal'),
        ('sales', 'Sales Journal'),
        ('purchases', 'Purchases Journal'),
        ('cash_receipts', 'Cash Receipts Journal'),
        ('cash_payments', 'Cash Payments Journal'),
        ('returns_inwards', 'Returns Inwards Journal'),
        ('returns_outwards', 'Returns Outwards Journal'),
        ('petty_cash', 'Petty Cash Journal'),
    ]
    
    entry_number = models.CharField(max_length=20, unique=True)
    journal_type = models.CharField(max_length=20, choices=JOURNAL_TYPES)
    date = models.DateField(auto_now_add=True)
    description = models.TextField()
    reference = models.CharField(max_length=50, blank=True)
    total_amount = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.entry_number} - {self.get_journal_type_display()}"

class JournalEntry(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='entries')
    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT)
    debit = models.IntegerField(default=0)
    credit = models.IntegerField(default=0)
    description = models.CharField(max_length=200, blank=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.journal.entry_number} - {self.account.name}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('expense', 'Expense'),
        ('payment', 'Payment'),
        ('receipt', 'Receipt'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
    ]
    
    TRANSACTION_CATEGORIES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
        ('contra_asset', 'Contra Asset'),
        ('contra_liability', 'Contra Liability'),
    ]
    
    date = models.DateField(auto_now_add=True)
    description = models.TextField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField(default=0)
    detected_category = models.CharField(max_length=20, choices=TRANSACTION_CATEGORIES, blank=True, null=True)
    detected_account = models.ForeignKey(LedgerAccount, on_delete=models.SET_NULL, null=True, blank=True)
    confidence_score = models.IntegerField(default=0)
    reference_number = models.CharField(max_length=50, blank=True)
    related_order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    related_expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True)
    related_asset = models.ForeignKey('Asset', on_delete=models.SET_NULL, null=True, blank=True)
    related_journal = models.ForeignKey('Journal', on_delete=models.SET_NULL, null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transactions')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.date} - {self.description[:50]}"


class Asset(models.Model):
    ASSET_TYPES = [
        ('current', 'Current Asset'),
        ('fixed', 'Fixed Asset'),
        ('intangible', 'Intangible Asset'),
        ('investment', 'Investment'),
    ]
    
    asset_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    purchase_date = models.DateField()
    purchase_price = models.IntegerField(default=0)
    current_value = models.IntegerField(default=0)
    depreciation_rate = models.IntegerField(default=0)
    accumulated_depreciation = models.IntegerField(default=0)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.asset_code} - {self.name}"


class Liability(models.Model):
    LIABILITY_TYPES = [
        ('current', 'Current Liability'),
        ('long_term', 'Long Term Liability'),
        ('contingent', 'Contingent Liability'),
    ]
    
    liability_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    liability_type = models.CharField(max_length=20, choices=LIABILITY_TYPES)
    amount = models.IntegerField(default=0)
    interest_rate = models.IntegerField(default=0)
    due_date = models.DateField()
    creditor = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.liability_code} - {self.name}"


class Equity(models.Model):
    EQUITY_TYPES = [
        ('capital', 'Capital'),
        ('drawings', 'Drawings'),
        ('reserves', 'Reserves'),
        ('retained_earnings', 'Retained Earnings'),
    ]
    
    equity_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    equity_type = models.CharField(max_length=20, choices=EQUITY_TYPES)
    amount = models.IntegerField(default=0)
    owner = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.equity_code} - {self.name}"
    

    # Add this to your laundry/models.py

class UserProfile(models.Model):
    """Extended user profile for role-based access"""
    ROLE_CHOICES = [
        ('manager', 'Manager/Owner'),
        ('staff', 'Staff'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_staff(self):
        return self.role == 'staff'
    
    class UserProfile(models.Model):
     ROLE_CHOICES = [
        ('manager', 'Manager/Owner'),
        ('staff', 'Staff'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=15, blank=True)
    registration_code = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_staff(self):
        return self.role == 'staff'