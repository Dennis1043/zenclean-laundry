from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Account(models.Model):
    """Flexible account system - users can create custom accounts"""
    
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    
    NORMAL_BALANCES = [
        ('D', 'Debit'),
        ('C', 'Credit'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    normal_balance = models.CharField(max_length=1, choices=NORMAL_BALANCES)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    parent_account = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['account_type', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_balance(self):
        return self.current_balance
    
    def update_balance(self):
        from django.db.models import Sum
        total_debit = JournalEntry.objects.filter(
            account=self, is_approved=True
        ).aggregate(Sum('debit'))['debit__sum'] or 0
        total_credit = JournalEntry.objects.filter(
            account=self, is_approved=True
        ).aggregate(Sum('credit'))['credit__sum'] or 0
        
        if self.normal_balance == 'D':
            self.current_balance = self.opening_balance + total_debit - total_credit
        else:
            self.current_balance = self.opening_balance + total_credit - total_debit
        self.save()
        return self.current_balance

class BusinessContext(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_context')
    business_name = models.CharField(max_length=200, default='My Business')
    business_type = models.CharField(max_length=50, default='sole_proprietorship')
    fiscal_year_start = models.DateField(default=timezone.now)
    currency = models.CharField(max_length=3, default='KES')
    custom_rules = models.JSONField(default=dict, blank=True)
    transaction_patterns = models.JSONField(default=dict, blank=True)
    common_descriptions = models.JSONField(default=dict, blank=True)
    user_corrections = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Context for {self.user.username}"

class NaturalLanguageTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reversed', 'Reversed'),
        ('edited', 'Edited'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    raw_text = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    analyzed_data = models.JSONField(default=dict, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    ai_reasoning = models.TextField(blank=True)
    suggested_journal = models.ForeignKey('Journal', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_transactions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    user_accepted = models.BooleanField(null=True, blank=True)
    user_correction = models.TextField(blank=True)
    documents = models.ManyToManyField('Document', blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.raw_text[:50]}..."
    
    def approve(self, user):
        self.status = 'approved'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.user_accepted = True
        self.save()
        if self.suggested_journal:
            self.suggested_journal.is_approved = True
            self.suggested_journal.approved_by = user
            self.suggested_journal.approved_at = timezone.now()
            self.suggested_journal.save()
            for entry in self.suggested_journal.entries.all():
                entry.is_approved = True
                entry.save()
                entry.account.update_balance()
    
    def reject(self, user, reason=""):
        self.status = 'rejected'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.user_accepted = False
        self.user_correction = reason
        self.save()

class Journal(models.Model):
    JOURNAL_TYPES = [
        ('general', 'General Journal'),
        ('sales', 'Sales Journal'),
        ('purchase', 'Purchase Journal'),
        ('cash_receipts', 'Cash Receipts Journal'),
        ('cash_payments', 'Cash Payments Journal'),
        ('reversal', 'Reversal Journal'),
    ]
    
    entry_number = models.CharField(max_length=50, unique=True)
    journal_type = models.CharField(max_length=20, choices=JOURNAL_TYPES, default='general')
    date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    natural_language_transaction = models.ForeignKey(NaturalLanguageTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    original_journal = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reversals')
    is_approved = models.BooleanField(default=False)
    is_reversal = models.BooleanField(default=False)
    is_void = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_journals')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_journals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.entry_number} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        if not self.entry_number:
            from datetime import datetime
            self.entry_number = f"JRN-{datetime.now().strftime('%Y%m%d')}-{Journal.objects.count() + 1:04d}"
        super().save(*args, **kwargs)

class JournalEntry(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='entries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.account.name}: Dr {self.debit} Cr {self.credit}"

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('receipt', 'Receipt'),
        ('invoice', 'Invoice'),
        ('bank_statement', 'Bank Statement'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.ForeignKey(NaturalLanguageTransaction, on_delete=models.CASCADE, null=True, blank=True, related_name='attached_documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='receipt')
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=100)
    ocr_text = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('reverse', 'Reverse'),
        ('view', 'View'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.model_name} #{self.object_id}"
