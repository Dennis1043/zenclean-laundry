from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from laundry.models import Transaction, JournalEntry, Journal, Asset, LedgerAccount
from laundry.transaction_analyzer import TransactionAnalyzer
from laundry.accounting_generator import AccountingEntryGenerator

class Command(BaseCommand):
    help = 'Reprocess all transactions with fixed accounting logic'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
        parser.add_argument(
            '--reset-first',
            action='store_true',
            help='Delete existing entries before reprocessing',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        reset_first = options.get('reset_first', False)
        
        self.stdout.write("=" * 60)
        self.stdout.write("REPROCESSING TRANSACTIONS")
        self.stdout.write("=" * 60)
        
        # Count existing data
        journal_count = Journal.objects.count()
        entry_count = JournalEntry.objects.count()
        asset_count = Asset.objects.count()
        transaction_count = Transaction.objects.filter(related_journal__isnull=True).count()
        
        self.stdout.write(f"Existing Journals: {journal_count}")
        self.stdout.write(f"Existing Journal Entries: {entry_count}")
        self.stdout.write(f"Existing Assets: {asset_count}")
        self.stdout.write(f"Unprocessed Transactions: {transaction_count}")
        
        if reset_first and not dry_run:
            self.stdout.write("\nResetting existing entries...")
            JournalEntry.objects.all().delete()
            Journal.objects.all().delete()
            Asset.objects.all().delete()
            Transaction.objects.update(related_journal=None, verified=False)
            LedgerAccount.objects.all().update(opening_balance=0, current_balance=0)
            self.stdout.write("✅ Reset complete")
        
        # Get transactions to process
        transactions = Transaction.objects.filter(related_journal__isnull=True)
        total = transactions.count()
        
        if total == 0:
            self.stdout.write("\nNo transactions to process.")
            return
        
        self.stdout.write(f"\nFound {total} transactions to process")
        
        if dry_run:
            self.stdout.write("\nDRY RUN - No changes made")
            self.stdout.write("First 10 transactions:")
            for trans in transactions[:10]:
                self.stdout.write(f"  - {trans.id}: {trans.description[:50]} ({trans.amount})")
            if total > 10:
                self.stdout.write(f"  ... and {total - 10} more")
            return
        
        processed = 0
        errors = 0
        analyzer = TransactionAnalyzer()
        
        self.stdout.write("\nProcessing transactions...")
        
        with transaction.atomic():
            for trans in transactions:
                try:
                    # Analyze the transaction
                    result = analyzer.analyze(
                        trans.description, 
                        trans.amount, 
                        trans.transaction_type
                    )
                    
                    # Update transaction with analysis
                    trans.detected_category = result['detected_category']
                    trans.detected_subcategory = result.get('detected_subcategory', '')
                    trans.confidence_score = result['confidence_score']
                    trans.save()
                    
                    # Generate accounting entries
                    generator = AccountingEntryGenerator(trans)
                    journal = generator.generate()
                    
                    processed += 1
                    if processed % 10 == 0:
                        self.stdout.write(f"  Processed {processed}/{total} transactions")
                        
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"  Error processing transaction {trans.id}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully processed {processed} transactions"))
        if errors > 0:
            self.stdout.write(self.style.WARNING(f"⚠️ {errors} transactions had errors"))
        
        # Show summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY AFTER REPROCESSING")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Journals: {Journal.objects.count()}")
        self.stdout.write(f"Journal Entries: {JournalEntry.objects.count()}")
        self.stdout.write(f"Assets: {Asset.objects.count()}")
        
        # Show trial balance
        self.stdout.write("\nTRIAL BALANCE:")
        self.stdout.write("-" * 60)
        
        total_debits = 0
        total_credits = 0
        
        for account in LedgerAccount.objects.filter(is_active=True).order_by('account_code'):
            from django.db.models import Sum
            total_debit = JournalEntry.objects.filter(account=account).aggregate(Sum('debit'))['debit__sum'] or 0
            total_credit = JournalEntry.objects.filter(account=account).aggregate(Sum('credit'))['credit__sum'] or 0
            
            if account.normal_balance == 'D':
                balance = account.opening_balance + total_debit - total_credit
            else:
                balance = account.opening_balance + total_credit - total_debit
            
            if balance != 0:
                self.stdout.write(f"  {account.account_code} {account.name}: {balance:,.2f}")
                if balance > 0:
                    if account.normal_balance == 'D':
                        total_debits += balance
                    else:
                        total_credits += balance
                else:
                    if account.normal_balance == 'D':
                        total_credits += abs(balance)
                    else:
                        total_debits += abs(balance)
        
        self.stdout.write("-" * 60)
        self.stdout.write(f"Total Debits: {total_debits:,.2f}")
        self.stdout.write(f"Total Credits: {total_credits:,.2f}")
        
        if abs(total_debits - total_credits) < 0.01:
            self.stdout.write(self.style.SUCCESS("✅ TRIAL BALANCE IS BALANCED!"))
        else:
            self.stdout.write(self.style.ERROR(f"⚠️ TRIAL BALANCE NOT BALANCED! Difference: {abs(total_debits - total_credits):,.2f}"))
