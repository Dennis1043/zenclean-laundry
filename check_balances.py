from laundry.models import LedgerAccount
print("=== ACCOUNT BALANCES ===")
for acc in LedgerAccount.objects.filter(is_active=True).order_by('code'):
    if acc.current_balance != 0:
        print(f"{acc.code} {acc.name}: {acc.current_balance:.2f} ({acc.normal_balance})")
