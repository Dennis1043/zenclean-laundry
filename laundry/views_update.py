@login_required
def update_order_status(request, order_id, status):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.status = status
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def update_order_payment(request, order_id, payment_status):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.payment_status = payment_status
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)
