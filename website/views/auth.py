"""Функции аутентификации и авторизации"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from datetime import datetime
from ..models import Record, Profile


def home(request):
    # Если пользователь не админ, показываем только его записи
    if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
        # Получаем профиль пользователя
        try:
            profile = Profile.objects.get(user=request.user)
            designer = profile.designer
        except Profile.DoesNotExist:
            designer = None
        
        if designer:
            # Пользователь — работник: показываем его задания
            records = Record.objects.filter(
                models.Q(designer=designer) |
                models.Q(designer_worker=designer) |
                models.Q(assembler_worker=designer)
            )
        else:
            # Пользователь — заказчик: показываем его заказы
            records = Record.objects.filter(customer=request.user)
            # Фолбэк: старые заказы без customer, но с совпадением имени/фамилии
            if (request.user.first_name or request.user.last_name):
                records = records | Record.objects.filter(
                    customer__isnull=True,
                    first_name__icontains=request.user.first_name or '',
                    last_name__icontains=request.user.last_name or ''
                )
    else:
        # Админы видят все записи
        records = Record.objects.all()
    
    # Фильтрация по статусу из GET параметра
    status_filter = request.GET.get('status', None)
    if status_filter:
        records = records.filter(status=status_filter)
    
    # Сортировка
    sort_by = request.GET.get('sort_by', 'id')
    sort_order = request.GET.get('sort_order', 'desc')
    prev_sort_by = request.GET.get('prev_sort_by', '')
    
    # Если переключились на другой столбец, сбрасываем направление сортировки
    if prev_sort_by and prev_sort_by != sort_by:
        sort_order = 'desc'
    
    # Применяем сортировку
    if sort_by == 'id':
        if sort_order == 'desc':
            records = records.order_by('-id')
        else:
            records = records.order_by('id')
    elif sort_by == 'created_at':
        if sort_order == 'desc':
            records = records.order_by('-created_at')
        else:
            records = records.order_by('created_at')
    else:
        records = records.order_by('-id')
        sort_order = 'desc'
    
    # Определяем следующий порядок сортировки для переключения
    next_sort_order = 'asc' if sort_order == 'desc' else 'desc'
    
    # Статистика по статусам за текущий месяц (с учетом фильтрации)
    now = datetime.now()
    current_month_records = records.filter(
        created_at__year=now.year,
        created_at__month=now.month
    )
    
    status_stats = {
        'total': current_month_records.count(),
        'otrisovka': current_month_records.filter(status='otrisovka').count(),
        'zhdem_material': current_month_records.filter(status='zhdem_material').count(),
        'priekhal_v_ceh': current_month_records.filter(status='priekhal_v_ceh').count(),
        'na_raspile': current_month_records.filter(status='na_raspile').count(),
        'zakaz_gotov': current_month_records.filter(status='zakaz_gotov').count(),
    }
    
    # Общая сумма по договорам
    total_contract_amount = sum(record.contract_amount for record in records if record.contract_amount)
    
    # Пагинация - показываем максимум 10 записей
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    per_page = 10
    total_records = records.count()
    total_pages = (total_records + per_page - 1) // per_page  # Округление вверх
    
    # Ограничиваем страницу
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    start = (page - 1) * per_page
    end = start + per_page
    records_page = records[start:end]
    
    # Вычисляем номера страниц для отображения (максимум 5)
    page_numbers = []
    if total_pages > 0:
        if total_pages <= 5:
            # Если страниц 5 или меньше, показываем все
            page_numbers = list(range(1, total_pages + 1))
        else:
            # Если страниц больше 5
            if page <= 3:
                # Если текущая страница в начале (1-3), показываем 1-5
                page_numbers = list(range(1, 6))
            elif page >= total_pages - 2:
                # Если текущая страница в конце, показываем последние 5
                page_numbers = list(range(total_pages - 4, total_pages + 1))
            else:
                # Если текущая страница в середине, показываем 5 страниц вокруг текущей
                # Например, если страница 7, показываем: 6, 7, 8, 9, 10
                page_numbers = list(range(page - 1, page + 4))
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You Have Been Logged In!")
            return redirect('home')
        else:
            messages.success(request, "There Was An Error Logging In, Please Try Again...")
            return redirect('home')
    else:
        return render(request, 'home.html', {
            'records': records_page,
            'status_stats': status_stats,
            'total_contract_amount': total_contract_amount,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'next_sort_order': next_sort_order,
            'status_filter': status_filter,
            'page': page,
            'total_pages': total_pages,
            'page_numbers': page_numbers,
            'total_records': total_records
        })


def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out...")
    return redirect('home')


def register_user(request):
    from ..forms import SignUpForm
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль для нового пользователя
            Profile.objects.get_or_create(user=user)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You Have Successfully Registered! Welcome!")
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

