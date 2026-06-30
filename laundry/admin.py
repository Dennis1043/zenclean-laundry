from django.contrib import admin
from .models import UserProfile, Customer, Order, Expense, Transaction
from .models import Account, BusinessContext, NaturalLanguageTransaction, Journal, JournalEntry, Document, AuditLog

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'location', 'total_orders', 'created_at']
    search_fields = ['name', 'phone']
    list_filter = ['created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'customer__name', 'customer__phone']
    readonly_fields = ['order_number', 'total_amount']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'category', 'amount', 'date', 'created_by']
    list_filter = ['category', 'date']
    search_fields = ['description']

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'normal_balance', 'current_balance', 'is_active']
    list_filter = ['account_type', 'is_active']
    search_fields = ['code', 'name']

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'journal_type', 'date', 'description', 'total_amount', 'is_approved']
    list_filter = ['journal_type', 'is_approved', 'created_at']
    search_fields = ['entry_number', 'description']

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['journal', 'account', 'debit', 'credit', 'is_approved']
    list_filter = ['is_approved']
    search_fields = ['account__name', 'description']

@admin.register(NaturalLanguageTransaction)
class NaturalLanguageTransactionAdmin(admin.ModelAdmin):
    list_display = ['raw_text', 'amount', 'confidence_score', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['raw_text']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_manager', 'is_staff']
    list_filter = ['role', 'is_manager']

@admin.register(BusinessContext)
class BusinessContextAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_name', 'business_type']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'user', 'created_at']
    list_filter = ['document_type']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'detected_category', 'confidence_score', 'created_at']
    list_filter = ['detected_category', 'created_at']
    search_fields = ['description']
