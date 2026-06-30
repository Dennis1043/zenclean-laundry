import re
from decimal import Decimal
from django.utils import timezone
from .transaction_analyzer import TransactionAnalyzer
from .accounting_generator import AccountingGenerator
from ..models import NaturalLanguageTransaction, BusinessContext, Account

class AIAccountingAssistant:
    """AI-powered accounting assistant"""
    
    def __init__(self, user):
        self.user = user
        self.context = self._get_or_create_context()
        self.analyzer = TransactionAnalyzer()
    
    def _get_or_create_context(self):
        context, _ = BusinessContext.objects.get_or_create(
            user=self.user,
            defaults={
                'business_name': 'My Business',
                'business_type': 'sole_proprietorship'
            }
        )
        return context
    
    def process_transaction(self, raw_text, amount=None, date=None):
        """Process a natural language transaction"""
        if amount is None:
            amount = self._extract_amount(raw_text)
        
        transaction = NaturalLanguageTransaction(
            user=self.user,
            raw_text=raw_text,
            amount=amount,
            date=date or timezone.now()
        )
        
        analysis = self.analyzer.analyze(raw_text, amount)
        
        transaction.analyzed_data = analysis
        transaction.confidence_score = analysis.get('confidence_score', 0)
        transaction.ai_reasoning = self._format_reasoning(analysis)
        transaction.save()
        
        if transaction.confidence_score >= 0.7:
            generator = AccountingGenerator(transaction)
            journal = generator.generate(analysis['suggested_entries'])
            transaction.suggested_journal = journal
            transaction.save()
        
        return transaction
    
    def _extract_amount(self, text):
        patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+\.\d{2})',
            r'(\d+)'
        ]
        all_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            all_matches.extend(matches)
        if all_matches:
            last_match = all_matches[-1]
            clean = last_match.replace(',', '')
            try:
                return Decimal(clean)
            except:
                return None
        return None
    
    def _format_reasoning(self, analysis):
        lines = []
        lines.append("**Transaction Analysis**")
        lines.append("")
        lines.append(f"**Category:** {analysis.get('detected_category', 'Unknown')}")
        lines.append(f"**Account Type:** {analysis.get('account_type', 'Unknown')}")
        lines.append(f"**Confidence:** {analysis.get('confidence_score', 0):.0%}")
        lines.append("")
        lines.append("**Reasoning:**")
        for reason in analysis.get('reasoning', []):
            lines.append(f"  {reason}")
        lines.append("")
        lines.append("**Suggested Journal Entry:**")
        for entry in analysis.get('suggested_entries', []):
            if entry.get('debit', 0) > 0:
                lines.append(f"  Debit:  {entry['account']} - {entry['debit']:.2f}")
            if entry.get('credit', 0) > 0:
                lines.append(f"  Credit: {entry['account']} - {entry['credit']:.2f}")
        return "\\n".join(lines)
    
    def get_dashboard_data(self):
        from django.db.models import Sum
        total_assets = Account.objects.filter(account_type='asset').aggregate(Sum('current_balance'))['current_balance__sum'] or 0
        total_liabilities = Account.objects.filter(account_type='liability').aggregate(Sum('current_balance'))['current_balance__sum'] or 0
        total_revenue = Account.objects.filter(account_type='revenue').aggregate(Sum('current_balance'))['current_balance__sum'] or 0
        total_expenses = Account.objects.filter(account_type='expense').aggregate(Sum('current_balance'))['current_balance__sum'] or 0
        pending = NaturalLanguageTransaction.objects.filter(user=self.user, status='pending').count()
        return {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_assets - total_liabilities,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': total_revenue - total_expenses,
            'pending_count': pending,
            'total_transactions': NaturalLanguageTransaction.objects.filter(user=self.user).count()
        }
    
    def answer_question(self, question):
        # Simplified version – just a placeholder
        return "I'm a simple assistant. I can help with basic transactions."
    
    def approve_transaction(self, transaction_id):
        try:
            trans = NaturalLanguageTransaction.objects.get(id=transaction_id, user=self.user)
            trans.approve(self.user)
            return trans, "Transaction approved and posted."
        except NaturalLanguageTransaction.DoesNotExist:
            return None, "Transaction not found."
    
    def reject_transaction(self, transaction_id, reason=""):
        try:
            trans = NaturalLanguageTransaction.objects.get(id=transaction_id, user=self.user)
            trans.reject(self.user, reason)
            return trans, "Transaction rejected."
        except NaturalLanguageTransaction.DoesNotExist:
            return None, "Transaction not found."
