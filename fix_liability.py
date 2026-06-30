import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from laundry.models import Liability, LedgerAccount, Journal, JournalEntry
from django.utils import timezone
from django.db.models import Sum

user = User.objects.get(username='dennis')

# ---- Calculate trial balance difference ----
total_debits = 0
total_credits = 0
for acc in LedgerAccount.objects.filter(is_active=True):
    if acc.current_balance > 0:
        if acc.normal_balance == 'D':
            total_debits += acc.current_balance
        else:
            total_credits += acc.current_balance
    elif acc.current_balance < 0:
        if acc.normal_balance == 'D':
            total_credits += abs(acc.current_balance)
        else:
            total_debits += abs(acc.current_balance)

diff = total_debits - total_credits
print(f"Total Debits: {total_debits:.2f}")
print(f"Total Credits: {total_credits:.2f}")
print(f"Difference (Debit - Credit): {diff:.2f}")

# ---- Create a liability if none exists ----
if Liability.objects.count() == 0 and diff > 0:
    liability = Liability.objects.create(
        liability_code='LIAB-BALANCE',
        name='Balancing Liability',
        liability_type='long_term',
        amount=diff,
        interest_rate=0,
        due_date=timezone.now().date() + timezone.timedelta(days=365),
        creditor='Auto',
        description='Created to balance trial balance'
    )
    print(f"✅ Created liability '{liability.name}' with amount {diff:.2f}")

# ---- Generate journal entries for all liabilities ----
cash = LedgerAccount.objects.get(code='1000')
for liability in Liability.objects.all():
    if liability.liability_type == 'current':
        account_code = '2000'
    else:
        account_code = '2100'
    liab_account, _ = LedgerAccount.objects.get_or_create(
        code=account_code,
        defaults={
            'name': f'{liability.name} Payable',
            'account_type': 'liability',
            'normal_balance': 'C',
            'opening_balance': 0,
            'current_balance': 0,
            'is_active': True
        }
    )
    if JournalEntry.objects.filter(journal__reference=liability.liability_code).exists():
        print(f"⏭️ Liability '{liability.name}' already has entries.")
        continue
    journal = Journal.objects.create(
        entry_number=f"LIAB-{liability.liability_code}",
        journal_type='general',
        date=timezone.now().date(),
        description=f"Liability: {liability.name}",
        reference=liability.liability_code,
        total_amount=liability.amount,
        created_by=user
    )
    JournalEntry.objects.create(
        journal=journal,
        account=cash,
        debit=liability.amount,
        credit=0,
        description=f"Cash received from {liability.creditor}",
        is_approved=True
    )
    JournalEntry.objects.create(
        journal=journal,
        account=liab_account,
        debit=0,
        credit=liability.amount,
        description=f"{liability.name} payable",
        is_approved=True
    )
    print(f"✅ Created journal for liability: {liability.name}")

# ---- Approve and update balances ----
JournalEntry.objects.all().update(is_approved=True)
for acc in LedgerAccount.objects.all():
    acc.update_balance()

print("\n✅ All balances updated.")
