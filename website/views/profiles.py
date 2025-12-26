"""Функции для работы с профилями"""
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Profile, Designer


def generate_verification_code():
    """Генерирует 6-значный код верификации"""
    return ''.join(random.choices(string.digits, k=6))


@login_required
def my_profile(request):
    """Страница профиля пользователя"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'generate_code':
            # Генерация кода верификации
            profile.verification_code = generate_verification_code()
            profile.telegram_verified = False
            profile.save()
            messages.success(
                request, 
                f'Код верификации: {profile.verification_code}. '
                f'Отправьте команду /verify {profile.verification_code} боту в Telegram.'
            )
            return redirect('my_profile')
        
        elif action == 'update_profile':
            # Обновление профиля
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('my_profile')
    
    return render(request, 'my_profile.html', {
        'profile': profile
    })


@login_required
def profiles_list(request):
    """Список всех профилей для управления (только для staff)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('home')
    
    from django.contrib.auth.models import User
    
    # Создаем профили для всех пользователей
    users = User.objects.all()
    for user in users:
        Profile.objects.get_or_create(user=user)
    
    # Получаем профили с предзагрузкой
    profiles = Profile.objects.select_related(
        'user', 
        'designer', 
        'designer__profession', 
        'designer__method'
    ).all()
    
    # Фильтрация
    filter_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '').strip()
    
    if filter_type == 'workers':
        profiles = profiles.exclude(designer__isnull=True)
    elif filter_type == 'customers':
        profiles = profiles.filter(designer__isnull=True).exclude(user__is_staff=True)
    elif filter_type == 'admins':
        profiles = profiles.filter(user__is_staff=True)
    
    if search_query:
        from django.db.models import Q
        profiles = profiles.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(designer__name__icontains=search_query) |
            Q(designer__surname__icontains=search_query)
        )
    
    profiles = profiles.order_by('user__username')
    
    # Обработка POST запросов
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        designer_id = request.POST.get('designer_id')
        
        if profile_id:
            profile = get_object_or_404(Profile, id=profile_id)
            if designer_id:
                designer = get_object_or_404(Designer, id=designer_id)
                profile.designer = designer
                messages.success(request, f'✓ {profile.user.username} → {designer.name} {designer.surname}')
            else:
                profile.designer = None
                messages.success(request, f'✓ Привязка удалена для {profile.user.username}')
            profile.save()
            return redirect('profiles_list')
    
    # Получаем всех дизайнеров
    designers = Designer.objects.select_related('profession', 'method').all()
    
    # Статистика
    stats = {
        'total': Profile.objects.count(),
        'workers': Profile.objects.exclude(designer__isnull=True).count(),
        'customers': Profile.objects.filter(designer__isnull=True).exclude(user__is_staff=True).count(),
        'admins': Profile.objects.filter(user__is_staff=True).count(),
    }
    
    return render(request, 'profiles_list.html', {
        'profiles': profiles,
        'designers': designers,
        'stats': stats,
        'current_filter': filter_type,
        'search_query': search_query,
    })

