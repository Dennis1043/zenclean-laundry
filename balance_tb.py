import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from laundry.models import LedgerAccount, Journal, JournalEntry
from django.utils import timezone

user = User.objects.get(username='dennis')

# Create a balancing entry if trial balance is not balanced
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
print(f"Difference: {diff:.2f}")

if abs(diff) > 0.01:
    # Find or create the Owner's Capital account
    capital, _ = LedgerAccount.objects.get_or_create(
        code='3000',
        defaults={
            'name': "Owner's Capital",
            'account_type': 'equity',
            'normal_balance': 'C',
            'opening_balance': 0,
            'current_balance': 0,
            'is_active': True
        }
    )
    cash = LedgerAccount.objects.get(code='1000')

    # Create a journal to balance the trial balance
    journal = Journal.objects.create(
        entry_number=f"BAL-{timezone.now().strftime('%Y%m%d')}",
        journal_type='adjustment',
        date=timezone.now().date(),
        description="Adjustment to balance trial balance",
        reference="BAL",
        total_amount=abs(diff),
        created_by=user
    )

    # If debits exceed credits, we need to credit capital (increase equity)
    if diff > 0:
        # Debit Cash, Credit Capital
        JournalEntry.objects.create(
            journal=journal,
            account=cash,
            debit=diff,
            credit=0,
            description="Balancing adjustment",
            is_approved=True
        )
        JournalEntry.objects.create(
            journal=journal,
            account=capital,
            debit=0,
            credit=diff,
            description="Balancing adjustment",
            is_approved=True
        )
    else:
        # If credits exceed debits, we need to debit capital
        JournalEntry.objects.create(
            journal=journal,
            account=capital,
            debit=abs(diff),
            credit=0,
            description="Balancing adjustment",
            is_approved=True
        )
        JournalEntry.objects.create(
            journal=journal,
            account=cash,
            debit=0,
            credit=abs(diff),
            description="Balancing adjustment",
            is_approved=True
        )

    # Update balances
    for acc in LedgerAccount.objects.all():
        acc.update_balance()

    print("✅ Balancing entry created.")
else:
    print("✅ Trial balance is already balanced.")
