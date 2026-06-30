from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Initialize default chart of accounts'

    def handle(self, *args, **options):
        # Get the model only when needed
        LedgerAccount = apps.get_model('laundry', 'LedgerAccount')
        
        default_accounts = [
            # Assets
            {'code': '1000', 'name': 'Cash', 'type': 'asset', 'balance': 'D'},
            {'code': '1100', 'name': 'Bank', 'type': 'asset', 'balance': 'D'},
            {'code': '1200', 'name': 'Accounts Receivable', 'type': 'asset', 'balance': 'D'},
            {'code': '1300', 'name': 'Inventory', 'type': 'asset', 'balance': 'D'},
            {'code': '1400', 'name': 'Fixed Assets', 'type': 'asset', 'balance': 'D'},
            {'code': '1500', 'name': 'Laundry Equipment', 'type': 'asset', 'balance': 'D'},
            
            # Liabilities
            {'code': '2000', 'name': 'Accounts Payable', 'type': 'liability', 'balance': 'C'},
            {'code': '2100', 'name': 'Bank Loan', 'type': 'liability', 'balance': 'C'},
            {'code': '2200', 'name': 'Accrued Expenses', 'type': 'liability', 'balance': 'C'},
            
            # Equity
            {'code': '3000', 'name': 'Capital', 'type': 'equity', 'balance': 'C'},
            {'code': '3100', 'name': 'Retained Earnings', 'type': 'equity', 'balance': 'C'},
            
            # Revenue
            {'code': '4000', 'name': 'Laundry Service Revenue', 'type': 'revenue', 'balance': 'C'},
            {'code': '4100', 'name': 'Delivery Revenue', 'type': 'revenue', 'balance': 'C'},
            
            # Expenses
            {'code': '5000', 'name': 'Salary Expense', 'type': 'expense', 'balance': 'D'},
            {'code': '5100', 'name': 'Rent Expense', 'type': 'expense', 'balance': 'D'},
            {'code': '5200', 'name': 'Utilities Expense', 'type': 'expense', 'balance': 'D'},
            {'code': '5300', 'name': 'Detergent Expense', 'type': 'expense', 'balance': 'D'},
            {'code': '5400', 'name': 'Water Expense', 'type': 'expense', 'balance': 'D'},
            {'code': '5500', 'name': 'Electricity Expense', 'type': 'expense', 'balance': 'D'},
            {'code': '5600', 'name': 'Maintenance Expense', 'type': 'expense', 'balance': 'D'},
            {'code': '5900', 'name': 'Miscellaneous Expense', 'type': 'expense', 'balance': 'D'},
        ]
        
        created_count = 0
        for acc in default_accounts:
            obj, created = LedgerAccount.objects.get_or_create(
                account_code=acc['code'],
                defaults={
                    'name': acc['name'],
                    'account_type': acc['type'],
                    'normal_balance': acc['balance'],
                    'opening_balance': 0,
                    'current_balance': 0,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {acc["code"]} - {acc["name"]}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'⏳ Already exists: {acc["code"]} - {acc["name"]}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Chart of accounts initialized successfully! ({created_count} new accounts created)'))
