"""
Представление для просмотра профиля заказчика и его заказов
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ..models import Record, Profile


@login_required
def customer_detail(request, user_id):
    """
    Страница заказчика с его заказами.
    Доступна админу/менеджеру или самому заказчику.
    """
    is_owner = request.user.id == user_id
    if not (request.user.is_staff or is_owner):
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('home')
    
    # Получаем пользователя
    customer = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=customer)
    
    # Получаем заказы заказчика (где он указан в поле customer)
    customer_records = Record.objects.filter(
        customer=customer
    ).select_related(
        'designer',
        'designer_worker',
        'assembler_worker'
    ).order_by('-created_at')
    
    # Также ищем заказы по имени (старые заказы без привязки к customer)
    if customer.first_name or customer.last_name:
        name_records = Record.objects.filter(
            customer__isnull=True  # Только заказы без привязанного заказчика
        ).filter(
            first_name__icontains=customer.first_name if customer.first_name else '',
            last_name__icontains=customer.last_name if customer.last_name else ''
        ).select_related(
            'designer',
            'designer_worker',
            'assembler_worker'
        ).order_by('-created_at')
        
        # Объединяем списки
        all_records = list(customer_records) + list(name_records)
        # Сортируем по дате
        all_records.sort(key=lambda x: x.created_at, reverse=True)
    else:
        all_records = customer_records
    
    # Статистика по заказам
    total_orders = len(all_records)
    total_amount = sum(r.contract_amount or 0 for r in all_records)
    
    # Заказы по статусам
    status_counts = {}
    for record in all_records:
        status_display = dict(Record.STATUS_CHOICES).get(record.status, record.status)
        status_counts[status_display] = status_counts.get(status_display, 0) + 1
    
    context = {
        'customer': customer,
        'profile': profile,
        'records': all_records,
        'total_orders': total_orders,
        'total_amount': total_amount,
        'status_counts': status_counts,
    }
    
    return render(request, 'customer_detail.html', context)

