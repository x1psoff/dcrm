"""Функции аналитики"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from datetime import datetime
import json
import calendar
from ..models import Record, Designer
from .calculations import calculate_record_margin, calculate_record_total_components, calculate_record_total_expenses


@login_required
def analytics_dashboard(request):
    """Панель аналитики с диаграммами и статистикой"""
    
    selected_year = request.GET.get('year')
    if selected_year:
        try:
            selected_year = int(selected_year)
        except (ValueError, TypeError):
            selected_year = None
    
    if not selected_year:
        selected_year = datetime.now().year
    
    selected_month = request.GET.get('month')
    if selected_month:
        try:
            selected_month = int(selected_month)
            if selected_month < 1 or selected_month > 12:
                selected_month = None
        except (ValueError, TypeError):
            selected_month = None
    
    available_years = Record.objects.dates('created_at', 'year', order='DESC')
    years_list = sorted([year.year for year in available_years], reverse=True)
    
    if not years_list:
        years_list = [datetime.now().year]
    
    if selected_year not in years_list:
        years_list.append(selected_year)
        years_list.sort(reverse=True)
    
    current_year = datetime.now().year
    if current_year not in years_list:
        years_list.append(current_year)
        years_list.sort(reverse=True)
    
    records = Record.objects.filter(created_at__year=selected_year).select_related(
        'designer', 'designer_worker', 'assembler_worker',
        'designer__method', 'designer_worker__method', 'assembler_worker__method'
    ).prefetch_related('files', 'unplanned_expenses', 'recordproduct_set__product')
    
    if selected_month:
        records = records.filter(created_at__month=selected_month)
    
    available_months = Record.objects.filter(created_at__year=selected_year).dates('created_at', 'month', order='ASC')
    months_list = sorted([month.month for month in available_months])
    
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    # Кэшируем результаты расчетов для всех записей
    margin_cache = {}
    for record in records:
        # Используем кэш на основе ID записи и времени обновления
        cache_key = f"record_margin_{record.id}_{record.updated_at.timestamp() if hasattr(record, 'updated_at') else record.created_at.timestamp()}"
        margin_data = cache.get(cache_key)
        if margin_data is None:
            margin_data = calculate_record_margin(record)
            # Кэшируем на 1 час
            cache.set(cache_key, margin_data, 3600)
        margin_cache[record.id] = margin_data
    
    # Анализ моржи по месяцам
    margin_by_month = []
    if selected_month:
        total_margin = 0
        for record in records:
            total_margin += margin_cache[record.id]['margin_total']
        margin_by_month.append({
            'month': month_names[selected_month],
            'margin': round(total_margin, 2)
        })
    else:
        year_records = Record.objects.filter(created_at__year=selected_year).select_related(
            'designer', 'designer_worker', 'assembler_worker'
        ).prefetch_related('files', 'unplanned_expenses', 'recordproduct_set__product')
        for month in range(1, 13):
            month_records = year_records.filter(created_at__month=month)
            total_margin = 0
            for record in month_records:
                # Используем кэш или вычисляем
                cache_key = f"record_margin_{record.id}_{record.updated_at.timestamp() if hasattr(record, 'updated_at') else record.created_at.timestamp()}"
                margin_data = cache.get(cache_key)
                if margin_data is None:
                    margin_data = calculate_record_margin(record)
                    cache.set(cache_key, margin_data, 3600)
                total_margin += margin_data['margin_total']
            margin_by_month.append({
                'month': calendar.month_name[month],
                'margin': round(total_margin, 2)
            })
    
    # Распределение моржи
    yura_margin = 0
    oleg_margin = 0
    total_margin = 0
    for record in records:
        margin_data = margin_cache[record.id]
        total_margin += margin_data['margin_total']
        yura_margin += margin_data['margin_yura']
        oleg_margin += margin_data['margin_oleg']
    
    margin_distribution = [
        {'name': 'Юра', 'value': round(yura_margin, 2)},
        {'name': 'Олег', 'value': round(oleg_margin, 2)}
    ]
    
    # Статистика по статусам
    status_stats = []
    for status_code, status_name in Record.STATUS_CHOICES:
        count = records.filter(status=status_code).count()
        status_stats.append({
            'name': status_name,
            'count': count,
            'code': status_code
        })
    
    # Топ проектировщиков - используем агрегацию вместо цикла
    designer_stats = []
    designer_counts = {}
    for record in records:
        if record.designer:
            designer_id = record.designer_id
            designer_counts[designer_id] = designer_counts.get(designer_id, 0) + 1
    
    # Загружаем дизайнеров одним запросом
    if designer_counts:
        designers_dict = {d.id: str(d) for d in Designer.objects.filter(id__in=designer_counts.keys())}
        for designer_id, count in designer_counts.items():
            if count > 0:
                designer_stats.append({
                    'name': designers_dict.get(designer_id, 'Неизвестно'),
                    'count': count
                })
    
    orders_with_margin = sum(1 for record in records if record.contract_amount)
    avg_margin = round(total_margin / orders_with_margin, 2) if orders_with_margin > 0 else 0
    
    total_orders = records.count()
    total_contract_amount = sum(float(record.contract_amount) for record in records if record.contract_amount)
    
    # Используем кэшированные данные или вычисляем один раз
    total_components_cost = 0
    total_expenses = 0
    for record in records:
        total_components_cost += calculate_record_total_components(record)
        total_expenses += calculate_record_total_expenses(record)
    
    # Анализ по дням недели
    weekday_stats = []
    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    for i, day in enumerate(weekdays):
        count = records.filter(created_at__week_day=i+2).count()
        weekday_stats.append({
            'day': day,
            'count': count
        })
    
    return render(request, 'analytics/dashboard.html', {
        'margin_by_month': json.dumps(margin_by_month, ensure_ascii=False),
        'margin_distribution': json.dumps(margin_distribution, ensure_ascii=False),
        'status_stats': json.dumps(status_stats, ensure_ascii=False),
        'designer_stats': json.dumps(designer_stats, ensure_ascii=False),
        'avg_margin': avg_margin,
        'total_orders': total_orders,
        'total_contract_amount': round(total_contract_amount, 2),
        'total_components_cost': round(total_components_cost, 2),
        'total_expenses': round(total_expenses, 2),
        'weekday_stats': json.dumps(weekday_stats, ensure_ascii=False),
        'current_year': selected_year,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'available_years': years_list,
        'available_months': months_list,
        'month_names': month_names,
        'yura_margin': round(yura_margin, 2),
        'oleg_margin': round(oleg_margin, 2),
        'total_margin': round(total_margin, 2)
    })

