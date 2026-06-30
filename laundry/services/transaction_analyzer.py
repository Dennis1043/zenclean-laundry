import re
from decimal import Decimal

class TransactionAnalyzer:
    """Analyzes natural language transactions and suggests accounting entries."""
    
    CAPITAL_KEYWORDS = {
        'started business', 'capital', 'owner contribution', 'investment', 
        'initial capital', 'business started', 'starting capital', 
        'owner invested', 'contributed capital', 'opening balance',
        'initial investment', 'equity', 'capital contribution',
        'brought into business', 'introduced capital', 'owner put in',
        'business started with', 'startup capital', 'seed capital'
    }
    
    def analyze(self, description, amount):
        """Analyze transaction and determine correct accounting treatment."""
        desc_lower = description.lower()
        result = {
            'description': description,
            'amount': float(amount) if amount else 0,
            'detected_category': None,
            'detected_subcategory': None,
            'account_type': None,
            'confidence_score': 0.00,
            'reasoning': [],
            'suggested_entries': []
        }
        
        # Check capital contribution
        if self._check_capital(desc_lower):
            result['detected_category'] = 'equity'
            result['detected_subcategory'] = 'owner_capital'
            result['account_type'] = "Owner's Capital"
            result['confidence_score'] = 0.95
            result['reasoning'].append("✅ Detected as Owner's Capital Contribution")
            result['reasoning'].append(f"📝 '{description}' indicates the owner is investing in the business")
            result['reasoning'].append("💰 This increases both Cash (Asset) and Capital (Equity)")
            result['suggested_entries'] = [
                {'account': 'Cash', 'debit': float(amount), 'credit': 0, 'description': 'Owner capital contribution'},
                {'account': "Owner's Capital", 'debit': 0, 'credit': float(amount), 'description': 'Capital from owner'}
            ]
            return result
        
        # Default to expense (simplified)
        result['detected_category'] = 'expense'
        result['detected_subcategory'] = 'miscellaneous'
        result['account_type'] = 'Miscellaneous Expense'
        result['confidence_score'] = 0.40
        result['reasoning'].append("⚠️ No clear category detected - defaulting to Miscellaneous Expense")
        result['reasoning'].append("💡 Please review and correct if needed")
        result['suggested_entries'] = [
            {'account': 'Miscellaneous Expense', 'debit': float(amount), 'credit': 0, 'description': 'Miscellaneous expense'},
            {'account': 'Cash', 'debit': 0, 'credit': float(amount), 'description': 'Payment for miscellaneous expense'}
        ]
        return result
    
    def _check_capital(self, description):
        """Check if description indicates capital contribution."""
        for keyword in self.CAPITAL_KEYWORDS:
            if keyword in description:
                return True
        if 'started' in description and 'business' in description:
            return True
        if 'capital' in description and ('invest' in description or 'contribute' in description):
            return True
        return False
