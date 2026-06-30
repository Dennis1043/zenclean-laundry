from decimal import Decimal
from django.utils import timezone
from .models import Journal, JournalEntry, Account, Transaction, Asset

class AccountingEntryGenerator:
    """
    Generates proper accounting entries from transactions with CORRECT debit/credit logic.
    All entries are created as approved, and account balances are updated immediately.
    """

    def __init__(self, transaction):
        self.transaction = transaction
        
        # Handle different transaction models
        if hasattr(transaction, 'raw_text'):  # NaturalLanguageTransaction
            self.description = transaction.raw_text
        elif hasattr(transaction, 'description'):  # Transaction model
            self.description = transaction.description
        else:
            self.description = str(transaction)
        
        self.amount = Decimal(str(transaction.amount))
        self.user = transaction.user if hasattr(transaction, 'user') else transaction.created_by
        
        # Extract category info
        if hasattr(transaction, 'analyzed_data') and transaction.analyzed_data:
            analysis = transaction.analyzed_data
            self.category = analysis.get('detected_category')
            self.subcategory = analysis.get('detected_subcategory')
            self.transaction_type = analysis.get('transaction_type', 'expense')
        else:
            self.category = getattr(transaction, 'detected_category', None)
            self.subcategory = getattr(transaction, 'detected_subcategory', '')
            self.transaction_type = getattr(transaction, 'transaction_type', 'expense')
    
    def generate(self):
        """Generate journal entries based on transaction type and category"""
        if not self.category:
            raise ValueError("Transaction category not set. Please analyze the transaction first.")
        
        # Create journal header
        journal = Journal.objects.create(
            entry_number=self._generate_entry_number(),
            journal_type='general',
            date=timezone.now().date(),
            description=f"Smart Entry: {self.description[:100]}",
            reference=str(self.transaction.id),
            total_amount=self.amount,
            created_by=self.user
        )
        
        # Determine the accounts based on transaction type and category
        entries = self._determine_entries()
        
        # Create journal entries (all approved)
        for entry_data in entries:
            JournalEntry.objects.create(
                journal=journal,
                account=entry_data['account'],
                debit=entry_data['debit'],
                credit=entry_data['credit'],
                description=entry_data.get('description', self.description[:200]),
                is_approved=True
            )
        
        # Update account balances for all affected accounts
        accounts_used = set(entry['account'] for entry in entries)
        for account in accounts_used:
            account.update_balance()
        
        # Link transaction to journal
        self.transaction.related_journal = journal
        self.transaction.save()
        
        # If asset, update asset record
        if self.category == 'asset':
            self._update_asset()
        
        return journal
    
    def _determine_entries(self):
        """Determine debit and credit entries based on transaction with CORRECT logic"""
        entries = []
        
        category = self.category
        subcategory = self.subcategory
        trans_type = self.transaction_type
        
        # Get default accounts (using get_or_create to avoid duplicates)
        cash_account = self._get_or_create_account('Cash', 'asset', 'D', '1000')
        accounts_receivable = self._get_or_create_account('Accounts Receivable', 'asset', 'D', '1200')
        accounts_payable = self._get_or_create_account('Accounts Payable', 'liability', 'C', '2000')
        
        # ============================================================
        # ASSET TRANSACTIONS
        # ============================================================
        if category == 'asset':
            if subcategory == 'fixed_asset':
                asset_account = self._get_or_create_asset_account()
                entries.append({
                    'account': asset_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Purchase of {self.description[:50]}"
                })
                entries.append({
                    'account': cash_account,
                    'debit': 0,
                    'credit': self.amount,
                    'description': f"Payment for {self.description[:50]}"
                })
            
            elif subcategory == 'current_asset':
                inventory_account = self._get_or_create_inventory_account()
                entries.append({
                    'account': inventory_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Purchase of {self.description[:50]}"
                })
                entries.append({
                    'account': cash_account,
                    'debit': 0,
                    'credit': self.amount,
                    'description': f"Payment for {self.description[:50]}"
                })
        
        # ============================================================
        # LIABILITY TRANSACTIONS
        # ============================================================
        elif category == 'liability':
            if subcategory == 'long_term_liability':
                liability_account = self._get_or_create_loan_account()
                entries.append({
                    'account': cash_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Loan received: {self.description[:50]}"
                })
                entries.append({
                    'account': liability_account,
                    'debit': 0,
                    'credit': self.amount,
                    'description': f"Loan payable: {self.description[:50]}"
                })
            
            elif subcategory == 'current_liability':
                expense_account = self._get_or_create_expense_account()
                entries.append({
                    'account': expense_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Expense incurred: {self.description[:50]}"
                })
                entries.append({
                    'account': accounts_payable,
                    'debit': 0,
                    'credit': self.amount,
                    'description': f"Liability for {self.description[:50]}"
                })
        
        # ============================================================
        # EQUITY TRANSACTIONS
        # ============================================================
        elif category == 'equity':
            if subcategory == 'owner_capital':
                capital_account = self._get_or_create_capital_account()
                entries.append({
                    'account': cash_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': 'Owner capital contribution'
                })
                entries.append({
                    'account': capital_account,
                    'debit': 0,
                    'credit': self.amount,
                    'description': 'Capital from owner'
                })
            elif subcategory == 'drawings':
                drawings_account = self._get_or_create_drawings_account()
                entries.append({
                    'account': drawings_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': 'Owner withdrawal'
                })
                entries.append({
                    'account': cash_account,
                    'debit': 0,
                    'credit': self.amount,
                    'description': 'Cash withdrawn by owner'
                })
        
        # ============================================================
        # REVENUE TRANSACTIONS
        # ============================================================
        elif category == 'revenue':
            revenue_account = self._get_or_create_revenue_account()
            is_credit = any(word in self.description.lower() for word in ['credit', 'unpaid', 'owing', 'receivable'])
            
            if is_credit:
                entries.append({
                    'account': accounts_receivable,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Credit sale: {self.description[:50]}"
                })
            else:
                entries.append({
                    'account': cash_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Cash received: {self.description[:50]}"
                })
            
            entries.append({
                'account': revenue_account,
                'debit': 0,
                'credit': self.amount,
                'description': f"Revenue from {self.description[:50]}"
            })
        
        # ============================================================
        # EXPENSE TRANSACTIONS
        # ============================================================
        elif category == 'expense':
            expense_account = self._get_or_create_expense_account()
            is_bill = any(word in self.description.lower() for word in ['bill', 'invoice', 'received', 'statement'])
            
            if is_bill:
                entries.append({
                    'account': expense_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Expense incurred: {self.description[:50]}"
                })
                entries.append({
                    'account': accounts_payable,
                    'debit': 0,
                    'credit': self.amount,
                    'description': f"Payable for {self.description[:50]}"
                })
            else:
                entries.append({
                    'account': expense_account,
                    'debit': self.amount,
                    'credit': 0,
                    'description': f"Expense: {self.description[:50]}"
                })
                entries.append({
                    'account': cash_account,
                    'debit': 0,
                    'credit': self.amount,
                    'description': f"Payment for {self.description[:50]}"
                })
        
        # ============================================================
        # DEFAULT - Miscellaneous Expense
        # ============================================================
        else:
            expense_account = self._get_or_create_miscellaneous_account()
            entries.append({
                'account': expense_account,
                'debit': self.amount,
                'credit': 0,
                'description': f"Transaction: {self.description[:50]}"
            })
            entries.append({
                'account': cash_account,
                'debit': 0,
                'credit': self.amount,
                'description': f"Payment: {self.description[:50]}"
            })
        
        return entries

    # ============================================================
    # ACCOUNT GETTER METHODS (with get_or_create by code)
    # ============================================================
    
    def _get_or_create_account(self, name, account_type, normal_balance, code=None):
        """Get or create an account by name and type, preferring code if provided."""
        try:
            if code:
                return Account.objects.get(code=code)
            return Account.objects.get(name__iexact=name)
        except Account.DoesNotExist:
            accounts = Account.objects.filter(name__icontains=name)
            if accounts.exists():
                return accounts.first()
        
        if not code:
            from django.db.models import Max
            max_code = Account.objects.filter(account_type=account_type).aggregate(Max('code'))['code__max']
            if max_code:
                num_part = int(max_code[1:]) + 1
                code = f"{account_type[0].upper()}{num_part:03d}"
            else:
                prefix = {'asset': '1', 'liability': '2', 'equity': '3', 'revenue': '4', 'expense': '5'}
                code = f"{prefix.get(account_type, '9')}001"
        
        return Account.objects.create(
            code=code,
            name=name,
            account_type=account_type,
            normal_balance=normal_balance,
            is_active=True,
            created_by=self.user
        )
    
    def _get_or_create_cash_account(self):
        return self._get_or_create_account('Cash', 'asset', 'D', '1000')
    
    def _get_or_create_accounts_receivable(self):
        return self._get_or_create_account('Accounts Receivable', 'asset', 'D', '1200')
    
    def _get_or_create_accounts_payable(self):
        return self._get_or_create_account('Accounts Payable', 'liability', 'C', '2000')
    
    def _get_or_create_capital_account(self):
        return self._get_or_create_account("Owner's Capital", 'equity', 'C', '3000')
    
    def _get_or_create_drawings_account(self):
        return self._get_or_create_account("Owner's Drawings", 'equity', 'D', '3200')
    
    def _get_or_create_asset_account(self):
        desc_lower = self.description.lower()
        if any(w in desc_lower for w in ['vehicle', 'car', 'van', 'truck']):
            return self._get_or_create_account('Vehicles', 'asset', 'D', '1600')
        elif any(w in desc_lower for w in ['building', 'property', 'land']):
            return self._get_or_create_account('Buildings', 'asset', 'D', '1700')
        elif any(w in desc_lower for w in ['computer', 'laptop', 'printer', 'scanner']):
            return self._get_or_create_account('Computer Equipment', 'asset', 'D', '1500')
        elif any(w in desc_lower for w in ['furniture', 'desk', 'chair', 'table', 'cabinet']):
            return self._get_or_create_account('Furniture & Fittings', 'asset', 'D', '1500')
        elif any(w in desc_lower for w in ['machine', 'machinery', 'equipment']):
            return self._get_or_create_account('Equipment', 'asset', 'D', '1400')
        return self._get_or_create_account('Equipment', 'asset', 'D', '1400')
    
    def _get_or_create_inventory_account(self):
        return self._get_or_create_account('Inventory', 'asset', 'D', '1300')
    
    def _get_or_create_loan_account(self):
        return self._get_or_create_account('Bank Loan', 'liability', 'C', '2100')
    
    def _get_or_create_expense_account(self):
        desc_lower = self.description.lower()
        if any(w in desc_lower for w in ['salary', 'wages']):
            return self._get_or_create_account('Salary Expense', 'expense', 'D', '5000')
        elif 'rent' in desc_lower:
            return self._get_or_create_account('Rent Expense', 'expense', 'D', '5100')
        elif any(w in desc_lower for w in ['electricity', 'power', 'token']):
            return self._get_or_create_account('Electricity Expense', 'expense', 'D', '5500')
        elif 'water' in desc_lower:
            return self._get_or_create_account('Water Expense', 'expense', 'D', '5400')
        elif any(w in desc_lower for w in ['detergent', 'soap']):
            return self._get_or_create_account('Supplies Expense', 'expense', 'D', '5300')
        elif any(w in desc_lower for w in ['maintenance', 'repair']):
            return self._get_or_create_account('Maintenance Expense', 'expense', 'D', '5600')
        elif 'insurance' in desc_lower:
            return self._get_or_create_account('Insurance Expense', 'expense', 'D', '5800')
        elif any(w in desc_lower for w in ['advertising', 'marketing']):
            return self._get_or_create_account('Advertising Expense', 'expense', 'D', '5800')
        return self._get_or_create_account('Miscellaneous Expense', 'expense', 'D', '5900')
    
    def _get_or_create_miscellaneous_account(self):
        return self._get_or_create_account('Miscellaneous Expense', 'expense', 'D', '5900')
    
    def _get_or_create_revenue_account(self):
        desc_lower = self.description.lower()
        if 'delivery' in desc_lower:
            return self._get_or_create_account('Delivery Revenue', 'revenue', 'C', '4100')
        elif 'express' in desc_lower:
            return self._get_or_create_account('Express Service Revenue', 'revenue', 'C', '4200')
        return self._get_or_create_account('Laundry Service Revenue', 'revenue', 'C', '4000')
    
    def _extract_asset_name(self):
        """Extract a meaningful asset name from the description."""
        words = self.description.split()
        stop_words = {'purchased', 'bought', 'new', 'equipment', 'machine', 'for', 'the', 'of', 'and', 'paid', 'purchase'}
        name_words = [w for w in words if w.lower() not in stop_words]
        return ' '.join(name_words[:4]) if name_words else 'Asset'
    
    def _update_asset(self):
        """Update or create an asset record based on the transaction."""
        asset_name = self._extract_asset_name()
        desc_lower = self.description.lower()
        if any(w in desc_lower for w in ['vehicle', 'car', 'van']):
            depreciation = 15.00
        elif any(w in desc_lower for w in ['computer', 'laptop', 'phone']):
            depreciation = 20.00
        elif any(w in desc_lower for w in ['machine', 'machinery', 'equipment']):
            depreciation = 10.00
        elif any(w in desc_lower for w in ['furniture', 'desk', 'chair']):
            depreciation = 10.00
        else:
            depreciation = 10.00
        
        asset, created = Asset.objects.get_or_create(
            name=asset_name,
            defaults={
                'asset_code': f"ASSET-{Asset.objects.count() + 1:04d}",
                'asset_type': 'fixed',
                'purchase_date': timezone.now().date(),
                'purchase_price': self.amount,
                'current_value': self.amount,
                'depreciation_rate': depreciation,
                'location': 'Main Store',
                'description': self.description
            }
        )
        if not created:
            asset.purchase_price = self.amount
            asset.current_value = self.amount
            asset.purchase_date = timezone.now().date()
            asset.save()
        print(f"Asset {'created' if created else 'updated'}: {asset_name} for {self.amount}")
    
    def _generate_entry_number(self):
        from datetime import datetime
        count = Journal.objects.count() + 1
        return f"JRN-{datetime.now().strftime('%Y%m%d')}-{count:04d}"

# Alias for backward compatibility with AI Assistant
AccountingGenerator = AccountingEntryGenerator