import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from laundry.models import Asset, Liability, Equity, LedgerAccount, Journal, JournalEntry
from django.utils import timezone

user = User.objects.get(username='dennis')

# Ensure Cash account exists
cash, _ = LedgerAccount.objects.get_or_create(
    code='1000',
    defaults={
        'name': 'Cash',
        'account_type': 'asset',
        'normal_balance': 'D',
        'opening_balance': 0,
        'current_balance': 0,
        'is_active': True
    }
)

# ---- Process Assets ----
print("=== Processing Assets ===")
for asset in Asset.objects.all():
    asset_account, _ = LedgerAccount.objects.get_or_create(
        code='1400',
        defaults={
            'name': 'Fixed Assets',
            'account_type': 'asset',
            'normal_balance': 'D',
            'opening_balance': 0,
            'current_balance': 0,
            'is_active': True
        }
    )
    if JournalEntry.objects.filter(journal__reference=asset.asset_code).exists():
        print(f"⏭️ Asset {asset.name} already has entries.")
        continue
    journal = Journal.objects.create(
        entry_number=f"AST-{asset.asset_code}",
        journal_type='purchases',
        date=asset.purchase_date or timezone.now().date(),
        description=f"Asset purchase: {asset.name}",
        reference=asset.asset_code,
        total_amount=asset.purchase_price,
        created_by=user
    )
    JournalEntry.objects.create(
        journal=journal,
        account=asset_account,
        debit=asset.purchase_price,
        credit=0,
        description=f"Purchase of {asset.name}",
        is_approved=True
    )
    JournalEntry.objects.create(
        journal=journal,
        account=cash,
        debit=0,
        credit=asset.purchase_price,
        description=f"Payment for {asset.name}",
        is_approved=True
    )
    print(f"✅ Created journal for asset: {asset.name}")

# ---- Process Liabilities ----
print("\n=== Processing Liabilities ===")
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
        print(f"⏭️ Liability {liability.name} already has entries.")
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

# ---- Process Equity ----
print("\n=== Processing Equity ===")
for equity in Equity.objects.all():
    if equity.equity_type == 'capital':
        account_code = '3000'
    else:
        account_code = '3100'
    eq_account, _ = LedgerAccount.objects.get_or_create(
        code=account_code,
        defaults={
            'name': equity.name,
            'account_type': 'equity',
            'normal_balance': 'C',
            'opening_balance': 0,
            'current_balance': 0,
            'is_active': True
        }
    )
    if JournalEntry.objects.filter(journal__reference=equity.equity_code).exists():
        print(f"⏭️ Equity {equity.name} already has entries.")
        continue
    journal = Journal.objects.create(
        entry_number=f"EQ-{equity.equity_code}",
        journal_type='general',
        date=timezone.now().date(),
        description=f"Equity: {equity.name}",
        reference=equity.equity_code,
        total_amount=equity.amount,
        created_by=user
    )
    JournalEntry.objects.create(
        journal=journal,
        account=cash,
        debit=equity.amount,
        credit=0,
        description=f"Capital contribution from {equity.owner}",
        is_approved=True
    )
    JournalEntry.objects.create(
        journal=journal,
        account=eq_account,
        debit=0,
        credit=equity.amount,
        description=f"{equity.name}",
        is_approved=True
    )
    print(f"✅ Created journal for equity: {equity.name}")

# ---- Approve and update balances ----
JournalEntry.objects.all().update(is_approved=True)

for acc in LedgerAccount.objects.all():
    acc.update_balance()

print("\n✅ Done.")
