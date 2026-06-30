# laundry/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def manager_required(view_func):
    """Decorator for views that only Manager/Owner can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            profile = request.user.profile
            if profile.is_manager:
                return view_func(request, *args, **kwargs)
        except:
            pass
        messages.error(request, 'Only Manager can access this page.')
        return redirect('dashboard')
    return wrapper

def staff_required(view_func):
    """Decorator for views that Staff can access (Dashboard, Orders, Customers)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            profile = request.user.profile
            # Both manager and staff can access
            if profile.is_manager or profile.is_staff:
                return view_func(request, *args, **kwargs)
        except:
            pass
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    return wrapper

def manager_or_staff_required(view_func):
    """Decorator for views that both Manager and Staff can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            profile = request.user.profile
            if profile.is_manager or profile.is_staff:
                return view_func(request, *args, **kwargs)
        except:
            pass
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    return wrapper