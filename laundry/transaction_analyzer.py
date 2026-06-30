import re
from decimal import Decimal
from .models import BusinessContext, Account

class TransactionAnalyzer:
    """
    AI-powered bookkeeping assistant that understands natural language,
    suggests double-entry accounting, and learns from user corrections.
    """

    # ============================================================
    # CATEGORY KEYWORDS (expandable)
    # ============================================================
    
    EQUITY_KEYWORDS = {
        'started business', 'capital', 'owner contribution', 'investment',
        'initial capital', 'business started', 'starting capital',
        'owner invested', 'contributed capital', 'opening balance',
        'initial investment', 'equity', 'capital contribution',
        'brought into business', 'introduced capital', 'owner put in',
        'business started with', 'startup capital', 'seed capital'
    }
    
    DRAWINGS_KEYWORDS = {
        'drawings', 'owner withdrawal', 'owner took', 'personal use',
        'owner paid', 'owner withdrew', 'private use', 'personal expense',
        'owner drawing', 'withdrawal by owner', 'took cash',
        'owner took money', 'personal withdrawal', 'owner withdrew cash'
    }
    
    FIXED_ASSET_KEYWORDS = {
        'equipment', 'machine', 'machinery', 'vehicle', 'car', 'van', 'truck',
        'furniture', 'building', 'land', 'property', 'computer', 'laptop',
        'printer', 'scanner', 'phone', 'fixture', 'construction',
        'warehouse', 'office', 'store', 'plant', 'tool', 'implement',
        'desk', 'chair', 'table', 'cabinet', 'shelf', 'counter',
        'bought', 'purchased', 'acquired', 'new equipment', 'new machine',
        'installation', 'hardware', 'software', 'license'
    }
    
    CURRENT_ASSET_KEYWORDS = {
        'inventory', 'stock', 'supplies', 'detergent', 'soap', 'chemical',
        'petty cash', 'prepaid', 'deposit', 'advance', 'merchandise',
        'goods', 'materials', 'raw materials', 'packaging'
    }
    
    RECEIVABLE_KEYWORDS = {
        'receivable', 'debtor', 'credit sale', 'sold on credit',
        'customer owes', 'amount receivable', 'unpaid sale',
        'invoice', 'outstanding payment', 'customer credit',
        'on account', 'credit customer', 'accounts receivable'
    }
    
    LONG_TERM_LIABILITY_KEYWORDS = {
        'loan', 'mortgage', 'debenture', 'bond', 'financing', 'term loan',
        'bank loan', 'equipment loan', 'vehicle loan', 'mortgage payable',
        'long term loan', 'business loan', 'funding', 'borrowed',
        'credit facility', 'overdraft''loan', 'mortgage', 'debenture', 'bond', 'financing', 'term loan',
        'bank loan', 'equipment loan', 'vehicle loan', 'mortgage payable',
        'long term loan', 'business loan', 'funding', 'borrowed',
        'credit facility', 'overdraft', 'loan from', 'borrow', 'kcb', 'equity bank'
    }
    
    CURRENT_LIABILITY_KEYWORDS = {
        'payable', 'creditor', 'supplier', 'accrued', 'unpaid', 'outstanding',
        'salary payable', 'wages payable', 'tax payable', 'vat payable',
        'utility bill', 'rent payable', 'interest payable', 'bill',
        'invoice received', 'supplier invoice', 'creditor payment',
        'amount owed', 'owe money', 'debt'
    }
    
    REVENUE_KEYWORDS = {
        'sale', 'sold', 'customer paid', 'customer payment',
        'laundry', 'dry cleaning', 'washing', 'ironing', 'folding',
        'service revenue', 'delivery', 'pickup', 'express', 'same day',
        'client paid', 'income', 'earned', 'collected', 'received payment',
        'cash sale', 'sales', 'service charge', 'transaction',
        'customer paid', 'client payment', 'payment received'
    }
    
    EXPENSE_KEYWORDS = {
        'salary', 'wages', 'rent', 'utility', 'electricity', 'power',
        'water', 'maintenance', 'repair', 'fuel', 'insurance',
        'advertising', 'marketing', 'stationery', 'office', 'cleaning',
        'token', 'paid', 'payment', 'expense', 'cost', 'fee', 'bill',
        'internet', 'phone', 'airtime', 'data', 'transport', 'travel',
        'meal', 'lunch', 'printing', 'photocopy', 'paper', 'ink', 'cartridge',
        # Supplies are now handled by current asset, but we keep them here for fallback
        'detergent', 'soap', 'supplies', 'cleaning supplies','downy','omo','salary', 'salaries', 'wages', 'payroll', 'casual', 'labour', 'staff',
    'rent', 'shop rent', 'lease',
    'utility', 'utilities', 'electricity', 'power', 'kplc', 'kenya power',
    'water', 'water bill', 'nairobi water', 'sewer', 'tokens', 'token',
    'maintenance', 'repair', 'repairs', 'service', 'servicing',
    'washing machine repair', 'dryer repair', 'plumbing', 'electrician',
    'fuel', 'petrol', 'diesel', 'transport', 'travel', 'delivery',
    'courier', 'uber', 'bolt', 'matatu',
    'insurance', 'premium',
    'advertising', 'marketing', 'promotion', 'facebook ads', 'google ads',
    'stationery', 'office', 'office supplies', 'paper', 'printing',
    'photocopy', 'receipt book', 'pens', 'ink', 'cartridge',
    'cleaning', 'cleaning supplies', 'detergent', 'washing powder',
    'soap', 'liquid detergent', 'omo', 'ariel', 'sunlight',
    'bleach', 'downy', 'comfort', 'fabric softener', 'starch',
    'stain remover', 'whitener', 'perfume', 'fragrance',
    'packaging', 'laundry bags', 'bags', 'hangers', 'labels',
    'garment tags',
    'internet', 'wifi', 'airtime', 'phone', 'data', 'bundles',
    'safaricom', 'airtel', 'telkom',
    'bank charges', 'bank fee', 'transaction fee',
    'mpesa charges', 'm-pesa', 'mobile money',
    'business permit', 'county permit', 'license', 'licence',
    'fire certificate',
    'accountant', 'bookkeeper', 'audit', 'lawyer', 'consultant',
    'security', 'guard', 'cctv', 'alarm',
    'gloves', 'apron', 'face mask', 'mask', 'protective clothing',
    'tea', 'coffee', 'snacks', 'refreshments', 'staff lunch',
    'drinking water',
    'expense', 'expenses', 'cost', 'costs', 'bill', 'bills',
    'fee', 'fees', 'paid', 'payment', 'pay', 'spent',
    'miscellaneous', 'other expense', 'general expense'
    }

    # Threshold for treating consumables as expenses (vs. assets)
    CONSUMABLE_EXPENSE_THRESHOLD = 5000

    # ============================================================
    # INITIALIZATION
    # ============================================================
    
    def __init__(self, user=None):
        self.user = user
        self.context = None
        if user:
            try:
                self.context = BusinessContext.objects.get(user=user)
            except BusinessContext.DoesNotExist:
                self.context = None
    
    # ============================================================
    # MAIN ANALYZE METHOD
    # ============================================================
    
    def analyze(self, description, amount=None):
        """
        Analyze a natural language transaction and return:
        - Detected category
        - Confidence score
        - Reasoning
        - Suggested journal entries
        - Follow-up questions (if any)
        """
        
        desc_lower = description.lower()
        amount = float(amount) if amount else None
        
        # Prepare result structure
        result = {
            'description': description,
            'amount': amount,
            'detected_category': None,
            'detected_subcategory': None,
            'account_type': None,
            'confidence_score': 0.0,
            'reasoning': [],
            'suggested_entries': [],
            'follow_up_questions': [],
            'user_correction_needed': False,
        }
        
        # ---- 1. Check for capital contributions ----
        if self._check_equity(desc_lower):
            return self._handle_equity(result, description, amount)
        
        # ---- 2. Check for drawings ----
        if self._check_drawings(desc_lower):
            return self._handle_drawings(result, description, amount)
        
        # ---- 3. Check for fixed assets ----
        if self._check_fixed_asset(desc_lower, amount):
            return self._handle_fixed_asset(result, description, amount)
        
        # ---- 4. Check for current assets (inventory, supplies) ----
        if self._check_current_asset(desc_lower):
            return self._handle_current_asset(result, description, amount)
        
        # ---- 5. Check for receivables (credit sales) ----
        if self._check_receivable(desc_lower):
            return self._handle_receivable(result, description, amount)
        
        # ---- 6. Check for long-term liabilities ----
        if self._check_long_term_liability(desc_lower):
            return self._handle_long_term_liability(result, description, amount)
        
        # ---- 7. Check for current liabilities ----
        if self._check_current_liability(desc_lower):
            return self._handle_current_liability(result, description, amount)
        
        # ---- 8. Check for revenue ----
        if self._check_revenue(desc_lower):
            return self._handle_revenue(result, description, amount)
        
        # ---- 9. Check for expenses ----
        if self._check_expense(desc_lower):
            return self._handle_expense(result, description, amount)
        
        # ---- 10. Default: miscellaneous expense ----
        return self._handle_default(result, description, amount)
    
    # ============================================================
    # DETECTION METHODS (boolean returns)
    # ============================================================
    
    def _check_equity(self, desc):
        for kw in self.EQUITY_KEYWORDS:
            if kw in desc:
                return True
        if 'started' in desc and 'business' in desc:
            return True
        if 'capital' in desc and ('invest' in desc or 'contribute' in desc):
            return True
        return False
    
    def _check_drawings(self, desc):
        for kw in self.DRAWINGS_KEYWORDS:
            if kw in desc:
                return True
        return False
    
    def _check_fixed_asset(self, desc, amount):
        score = 0
        for kw in self.FIXED_ASSET_KEYWORDS:
            if kw in desc:
                score += 1
        if amount and amount > 20000:
            score += 1
        return score >= 2
    
    def _check_current_asset(self, desc):
        for kw in self.CURRENT_ASSET_KEYWORDS:
            if kw in desc:
                return True
        return False
    
    def _check_receivable(self, desc):
        for kw in self.RECEIVABLE_KEYWORDS:
            if kw in desc:
                return True
        return False
    
    def _check_long_term_liability(self, desc):
        for kw in self.LONG_TERM_LIABILITY_KEYWORDS:
            if kw in desc:
                return True
        return False
    
    def _check_current_liability(self, desc):
        for kw in self.CURRENT_LIABILITY_KEYWORDS:
            if kw in desc:
                return True
        return False
    
    def _check_revenue(self, desc):
        score = 0
        for kw in self.REVENUE_KEYWORDS:
            if kw in desc:
                score += 1
        return score >= 2
    
    def _check_expense(self, desc):
        score = 0
        for kw in self.EXPENSE_KEYWORDS:
            if kw in desc:
                score += 1
        return score >= 2
    
    # ============================================================
    # HANDLER METHODS (populate result)
    # ============================================================
    
    def _handle_equity(self, result, description, amount):
        result['detected_category'] = 'equity'
        result['detected_subcategory'] = 'owner_capital'
        result['account_type'] = "Owner's Capital"
        result['confidence_score'] = 0.95
        result['reasoning'].append("✅ Detected as Owner's Capital Contribution")
        result['reasoning'].append(f"📝 '{description}' indicates the owner is investing in the business")
        result['reasoning'].append("💰 This increases both Cash (Asset) and Capital (Equity)")
        result['suggested_entries'] = [
            {'account': 'Cash', 'debit': amount, 'credit': 0, 'description': 'Owner capital contribution'},
            {'account': "Owner's Capital", 'debit': 0, 'credit': amount, 'description': 'Capital from owner'}
        ]
        return result
    
    def _handle_drawings(self, result, description, amount):
        result['detected_category'] = 'equity'
        result['detected_subcategory'] = 'drawings'
        result['account_type'] = "Owner's Drawings"
        result['confidence_score'] = 0.90
        result['reasoning'].append("✅ Detected as Owner's Drawings")
        result['reasoning'].append(f"📝 '{description}' indicates the owner is taking money from the business")
        result['reasoning'].append("💰 This decreases Cash (Asset) and increases Drawings (Equity)")
        result['suggested_entries'] = [
            {'account': "Owner's Drawings", 'debit': amount, 'credit': 0, 'description': 'Owner withdrawal'},
            {'account': 'Cash', 'debit': 0, 'credit': amount, 'description': 'Cash withdrawn by owner'}
        ]
        return result
    
    def _handle_fixed_asset(self, result, description, amount):
        asset_type = self._determine_asset_type(description)
        result['detected_category'] = 'asset'
        result['detected_subcategory'] = 'fixed_asset'
        result['account_type'] = asset_type
        result['confidence_score'] = 0.85
        result['reasoning'].append(f"✅ Detected as Fixed Asset Purchase: {asset_type}")
        result['reasoning'].append(f"📝 '{description}' indicates purchase of a long-term asset")
        result['reasoning'].append("💰 This increases Assets (Equipment) and decreases Cash")
        result['suggested_entries'] = [
            {'account': asset_type, 'debit': amount, 'credit': 0, 'description': f'Purchase of {asset_type}'},
            {'account': 'Cash', 'debit': 0, 'credit': amount, 'description': f'Payment for {asset_type}'}
        ]
        return result
    
    def _handle_current_asset(self, result, description, amount):
        # If amount is small and the item is a consumable, treat as expense
        if amount <= self.CONSUMABLE_EXPENSE_THRESHOLD:
            expense_type = 'Supplies Expense'
            result['detected_category'] = 'expense'
            result['detected_subcategory'] = 'supplies'
            result['account_type'] = expense_type
            result['confidence_score'] = 0.85
            result['reasoning'].append("✅ Detected as Supplies Expense (small consumable purchase)")
            result['reasoning'].append(f"📝 '{description}' indicates purchase of consumable supplies")
            result['reasoning'].append("💰 This increases Expense and decreases Cash")
            result['suggested_entries'] = [
                {'account': expense_type, 'debit': amount, 'credit': 0, 'description': 'Purchase of supplies'},
                {'account': 'Cash', 'debit': 0, 'credit': amount, 'description': 'Payment for supplies'}
            ]
            return result
        
        # Otherwise treat as current asset
        asset_type = 'Inventory'
        if 'detergent' in description or 'soap' in description:
            asset_type = 'Supplies Inventory'
        elif 'supplies' in description:
            asset_type = 'Office Supplies'
        result['detected_category'] = 'asset'
        result['detected_subcategory'] = 'current_asset'
        result['account_type'] = asset_type
        result['confidence_score'] = 0.80
        result['reasoning'].append(f"✅ Detected as Current Asset Purchase: {asset_type}")
        result['reasoning'].append(f"📝 '{description}' indicates purchase of inventory/supplies")
        result['reasoning'].append("💰 This increases Assets (Inventory) and decreases Cash")
        result['suggested_entries'] = [
            {'account': asset_type, 'debit': amount, 'credit': 0, 'description': f'Purchase of {asset_type}'},
            {'account': 'Cash', 'debit': 0, 'credit': amount, 'description': f'Payment for {asset_type}'}
        ]
        return result
    
    def _handle_receivable(self, result, description, amount):
        revenue_type = self._determine_revenue_type(description)
        result['detected_category'] = 'asset'
        result['detected_subcategory'] = 'receivable'
        result['account_type'] = 'Accounts Receivable'
        result['confidence_score'] = 0.85
        result['reasoning'].append("✅ Detected as Credit Sale (Accounts Receivable)")
        result['reasoning'].append(f"📝 '{description}' indicates a sale on credit")
        result['reasoning'].append("💰 This increases Accounts Receivable (Asset) and Revenue")
        result['suggested_entries'] = [
            {'account': 'Accounts Receivable', 'debit': amount, 'credit': 0, 'description': 'Credit sale'},
            {'account': revenue_type, 'debit': 0, 'credit': amount, 'description': 'Revenue from credit sale'}
        ]
        return result
    
    def _handle_long_term_liability(self, result, description, amount):
        liability_type = 'Loan Payable'
        if 'mortgage' in description:
            liability_type = 'Mortgage Payable'
        result['detected_category'] = 'liability'
        result['detected_subcategory'] = 'long_term_liability'
        result['account_type'] = liability_type
        result['confidence_score'] = 0.90
        result['reasoning'].append(f"✅ Detected as Long-Term Liability: {liability_type}")
        result['reasoning'].append(f"📝 '{description}' indicates a loan received")
        result['reasoning'].append("💰 This increases Cash (Asset) and Loan Payable (Liability)")
        result['suggested_entries'] = [
            {'account': 'Cash', 'debit': amount, 'credit': 0, 'description': 'Loan received'},
            {'account': liability_type, 'debit': 0, 'credit': amount, 'description': 'Loan payable'}
        ]
        return result
    
    def _handle_current_liability(self, result, description, amount):
        expense_type = self._determine_expense_type(description)
        liability_type = self._determine_liability_type(description)
        result['detected_category'] = 'liability'
        result['detected_subcategory'] = 'current_liability'
        result['account_type'] = liability_type
        result['confidence_score'] = 0.80
        result['reasoning'].append(f"✅ Detected as Current Liability: {liability_type}")
        result['reasoning'].append(f"📝 '{description}' indicates a bill received but not yet paid")
        result['reasoning'].append("💰 This increases Expense and Liability (Accounts Payable)")
        result['suggested_entries'] = [
            {'account': expense_type, 'debit': amount, 'credit': 0, 'description': 'Expense incurred'},
            {'account': liability_type, 'debit': 0, 'credit': amount, 'description': f'Liability for {expense_type}'}
        ]
        return result
    
    def _handle_revenue(self, result, description, amount):
        revenue_type = self._determine_revenue_type(description)
        is_credit = any(w in description for w in ['credit', 'unpaid', 'owing'])
        result['detected_category'] = 'revenue'
        result['detected_subcategory'] = 'service_revenue'
        result['account_type'] = revenue_type
        result['confidence_score'] = 0.85
        result['reasoning'].append(f"✅ Detected as Revenue: {revenue_type}")
        result['reasoning'].append(f"📝 '{description}' indicates income earned")
        if is_credit:
            result['reasoning'].append("💰 This is a credit sale - increases Accounts Receivable and Revenue")
            result['suggested_entries'] = [
                {'account': 'Accounts Receivable', 'debit': amount, 'credit': 0, 'description': 'Credit sale'},
                {'account': revenue_type, 'debit': 0, 'credit': amount, 'description': 'Revenue from service'}
            ]
        else:
            result['reasoning'].append("💰 This increases Cash (Asset) and Revenue")
            result['suggested_entries'] = [
                {'account': 'Cash', 'debit': amount, 'credit': 0, 'description': 'Cash received'},
                {'account': revenue_type, 'debit': 0, 'credit': amount, 'description': 'Revenue from service'}
            ]
        return result
    
    def _handle_expense(self, result, description, amount):
        expense_type = self._determine_expense_type(description)
        is_bill = any(w in description for w in ['bill', 'invoice', 'received', 'statement'])
        result['detected_category'] = 'expense'
        result['detected_subcategory'] = 'operating_expense'
        result['account_type'] = expense_type
        result['confidence_score'] = 0.80
        result['reasoning'].append(f"✅ Detected as Expense: {expense_type}")
        result['reasoning'].append(f"📝 '{description}' indicates a payment or cost incurred")
        if is_bill:
            result['reasoning'].append("💰 This is a bill received - increases Expense and Accounts Payable")
            result['suggested_entries'] = [
                {'account': expense_type, 'debit': amount, 'credit': 0, 'description': 'Expense incurred'},
                {'account': 'Accounts Payable', 'debit': 0, 'credit': amount, 'description': f'Liability for {expense_type}'}
            ]
        else:
            result['reasoning'].append("💰 This increases Expense and decreases Cash")
            result['suggested_entries'] = [
                {'account': expense_type, 'debit': amount, 'credit': 0, 'description': 'Expense payment'},
                {'account': 'Cash', 'debit': 0, 'credit': amount, 'description': f'Payment for {expense_type}'}
            ]
        return result
    
    def _handle_default(self, result, description, amount):
        result['detected_category'] = 'expense'
        result['detected_subcategory'] = 'miscellaneous'
        result['account_type'] = 'Miscellaneous Expense'
        result['confidence_score'] = 0.40
        result['reasoning'].append("⚠️ No clear category detected - defaulting to Miscellaneous Expense")
        result['reasoning'].append("💡 Please review and correct if needed")
        result['suggested_entries'] = [
            {'account': 'Miscellaneous Expense', 'debit': amount, 'credit': 0, 'description': 'Miscellaneous expense'},
            {'account': 'Cash', 'debit': 0, 'credit': amount, 'description': 'Payment for miscellaneous expense'}
        ]
        return result
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _determine_asset_type(self, description):
        desc = description.lower()
        if any(w in desc for w in ['machine', 'machinery', 'equipment']):
            return 'Equipment'
        elif any(w in desc for w in ['vehicle', 'car', 'van', 'truck']):
            return 'Vehicles'
        elif any(w in desc for w in ['building', 'property', 'land']):
            return 'Buildings'
        elif any(w in desc for w in ['computer', 'laptop', 'printer']):
            return 'Computer Equipment'
        elif any(w in desc for w in ['furniture', 'desk', 'chair', 'table']):
            return 'Furniture & Fittings'
        return 'Equipment'
    
    def _determine_expense_type(self, description):
        desc = description.lower()
        if any(w in desc for w in ['salary', 'wages']):
            return 'Salary Expense'
        elif 'rent' in desc:
            return 'Rent Expense'
        elif any(w in desc for w in ['electricity', 'power', 'token']):
            return 'Electricity Expense'
        elif 'water' in desc:
            return 'Water Expense'
        elif any(w in desc for w in ['maintenance', 'repair']):
            return 'Maintenance Expense'
        elif 'insurance' in desc:
            return 'Insurance Expense'
        elif any(w in desc for w in ['advertising', 'marketing']):
            return 'Advertising Expense'
        elif 'transport' in desc or 'travel' in desc:
            return 'Transport Expense'
        elif any(w in desc for w in ['detergent', 'soap', 'supplies']):
            return 'Supplies Expense'
        return 'Operating Expense'
    
    def _determine_revenue_type(self, description):
        desc = description.lower()
        if 'delivery' in desc:
            return 'Delivery Revenue'
        elif 'express' in desc:
            return 'Express Service Revenue'
        return 'Service Revenue'
    
    def _determine_liability_type(self, description):
        desc = description.lower()
        if any(w in desc for w in ['salary', 'wages']):
            return 'Salaries Payable'
        elif 'tax' in desc:
            return 'Tax Payable'
        elif any(w in desc for w in ['utility', 'electricity', 'water']):
            return 'Utilities Payable'
        return 'Accounts Payable'