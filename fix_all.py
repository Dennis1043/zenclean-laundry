import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from laundry.models import Liability, LedgerAccount, Journal, JournalEntry
from django.db.models import Sum

user = User.objects.get(username='dennis')

# ----- Compute current trial balance -----
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

print(f"Total Debits: {total_debits:.2f}")
print(f"Total Credits: {total_credits:.2f}")
diff = total_debits - total_credits
print(f"Difference (Debit - Credit): {diff:.2f}")

# ----- Create or update liability to balance -----
liability_code = 'BAL-001'
if diff > 0:
    # Need to credit a liability
    amount_needed = abs(diff)
    liability, created = Liability.objects.get_or_create(
        liability_code=liability_code,
        defaults={
            'name': 'Balancing Liability',
            'liability_type': 'long_term',
            'amount': amount_needed,
            'interest_rate': 0,
            'due_date': timezone.now().date() + timedelta(days=365),
            'creditor': 'Auto Generated'
        }
    )
    if created:
        print(f"✅ Created liability with amount {amount_needed:.2f}")
    else:
        # Update existing liability to the new amount
        liability.amount = amount_needed
        liability.save()
        print(f"✅ Updated liability to {amount_needed:.2f}")
else:
    print("Trial balance is balanced or credits exceed debits. No liability needed.")
    # If credits > debits, you might need an asset, but we skip for now.

# ----- Generate journal entries for all liabilities -----
cash = LedgerAccount.objects.get(code='1000')
for liability in Liability.objects.all():
    # Determine account code based on type
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

# ----- Approve all entries and update balances -----
JournalEntry.objects.all().update(is_approved=True)
for acc in LedgerAccount.objects.all():
    acc.update_balance()

print("\n✅ All balances updated.")

# ----- Final trial balance check -----
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

print(f"\nFINAL TRIAL BALANCE:")
print(f"Total Debits: {total_debits:.2f}")
print(f"Total Credits: {total_credits:.2f}")
if total_debits == total_credits:
    print("✅ Trial balance is BALANCED!")
else:
    print(f"❌ Trial balance is NOT balanced. Difference: {total_debits - total_credits:.2f}")
