from laundry.models import Liability, JournalEntry

for l in Liability.objects.all():
    print(l.name, l.liability_code, l.amount)
    if JournalEntry.objects.filter(journal__reference=l.liability_code).exists():
        print('  -> Has journal entry.')
    else:
        print('  -> Missing journal entry.')
