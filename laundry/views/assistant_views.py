from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from ..services.ai_assistant import AIAccountingAssistant
from ..models import NaturalLanguageTransaction, Account

@login_required
def assistant_dashboard(request):
    assistant = AIAccountingAssistant(request.user)
    data = assistant.get_dashboard_data()
    context = {
        'data': data,
        'pending_transactions': NaturalLanguageTransaction.objects.filter(
            user=request.user, 
            status='pending'
        ).order_by('-created_at')[:20]
    }
    return render(request, 'assistant/dashboard.html', context)

@login_required
def process_transaction(request):
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        amount = request.POST.get('amount', '').strip()
        if not text:
            messages.error(request, 'Please describe the transaction.')
            return redirect('assistant_dashboard')
        amount = float(amount) if amount else None
        assistant = AIAccountingAssistant(request.user)
        transaction = assistant.process_transaction(text, amount)
        messages.success(request, 'Transaction analyzed successfully!')
        return redirect('assistant_review', transaction_id=transaction.id)
    return redirect('assistant_dashboard')

@login_required
def review_transaction(request, transaction_id):
    transaction = get_object_or_404(NaturalLanguageTransaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        correction = request.POST.get('correction', '').strip()
        assistant = AIAccountingAssistant(request.user)
        if action == 'approve':
            trans, message = assistant.approve_transaction(transaction_id)
            messages.success(request, message)
            return redirect('assistant_dashboard')
        elif action == 'reject':
            trans, message = assistant.reject_transaction(transaction_id, correction)
            messages.warning(request, message)
            return redirect('assistant_dashboard')
    context = {
        'transaction': transaction,
        'journal_entries': transaction.suggested_journal.entries.all() if transaction.suggested_journal else []
    }
    return render(request, 'assistant/review.html', context)

@login_required
def ask_assistant(request):
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        if not question:
            return JsonResponse({'error': 'Please enter a question.'}, status=400)
        assistant = AIAccountingAssistant(request.user)
        answer = assistant.answer_question(question)
        return JsonResponse({'question': question, 'answer': answer})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def transaction_history(request):
    transactions = NaturalLanguageTransaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'assistant/history.html', {'transactions': transactions})

@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(NaturalLanguageTransaction, id=transaction_id, user=request.user)
    return render(request, 'assistant/detail.html', {
        'transaction': transaction,
        'journal_entries': transaction.suggested_journal.entries.all() if transaction.suggested_journal else []
    })
