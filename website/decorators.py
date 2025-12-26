"""
Декораторы для проверки прав доступа пользователей
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile


def worker_required(view_func):
    """Декоратор для проверки, что пользователь является работником"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.is_worker or request.user.is_staff:
                return view_func(request, *args, **kwargs)
        except Profile.DoesNotExist:
            pass
        
        messages.error(request, 'Доступ запрещен. Эта страница доступна только для работников.')
        return redirect('home')
    
    return _wrapped_view


def customer_required(view_func):
    """Декоратор для проверки, что пользователь является заказчиком"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.is_customer or request.user.is_staff:
                return view_func(request, *args, **kwargs)
        except Profile.DoesNotExist:
            pass
        
        messages.error(request, 'Доступ запрещен. Эта страница доступна только для заказчиков.')
        return redirect('home')
    
    return _wrapped_view


def staff_or_worker_required(view_func):
    """Декоратор для проверки, что пользователь является администратором или работником"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.is_worker:
                return view_func(request, *args, **kwargs)
        except Profile.DoesNotExist:
            pass
        
        messages.error(request, 'Доступ запрещен. Эта страница доступна только для сотрудников и работников.')
        return redirect('home')
    
    return _wrapped_view

