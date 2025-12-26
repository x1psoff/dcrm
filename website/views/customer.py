"""
Представления для заказчиков
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Record, Profile
from ..decorators import customer_required


@login_required
def customer_orders(request):
    """Список заказов для заказчика"""
    # Получаем профиль пользователя
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        Profile.objects.create(user=request.user)
        profile = Profile.objects.get(user=request.user)
    
    # Если пользователь - работник или админ, показываем все заказы
    if request.user.is_staff or profile.is_worker:
        records = Record.objects.all().order_by('-created_at')
    else:
        # Для заказчиков показываем только их заказы
        # Фильтруем по имени пользователя или другим критериям
        user_full_name = request.user.get_full_name()
        records = Record.objects.filter(
            first_name__icontains=user_full_name.split()[0] if user_full_name else request.user.username
        ).order_by('-created_at')
    
    context = {
        'records': records,
        'profile': profile,
    }
    return render(request, 'customer_orders.html', context)


@login_required
def customer_order_detail(request, pk):
    """Детальная информация о заказе для заказчика"""
    record = get_object_or_404(Record, id=pk)
    
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    
    # Проверка прав доступа
    if not request.user.is_staff and profile and not profile.is_worker:
        # Заказчик может видеть только свои заказы
        user_full_name = request.user.get_full_name()
        if user_full_name:
            first_name = user_full_name.split()[0]
            if record.first_name.lower() != first_name.lower():
                return render(request, 'error.html', {
                    'error_message': 'У вас нет доступа к этому заказу'
                })
    
    context = {
        'record': record,
        'profile': profile,
    }
    return render(request, 'customer_order_detail.html', context)

