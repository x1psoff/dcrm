"""Функции для работы с выплатами работникам"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from ..models import Record, Designer, WorkerPayment
from ..utils.csv_cache import get_record_files_area


@login_required
def payments_page(request):
    """Страница выплат работникам"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для просмотра выплат')
        return redirect('home')
    
    # Получаем всех работников
    workers = Designer.objects.select_related('profession', 'method').all().order_by('surname', 'name')
    
    # Данные для каждого работника
    workers_data = []
    
    for worker in workers:
        # Находим все записи, где работник участвует
        records_as_designer = Record.objects.filter(designer=worker).select_related('designer', 'designer_worker', 'assembler_worker')
        records_as_designer_worker = Record.objects.filter(designer_worker=worker).select_related('designer', 'designer_worker', 'assembler_worker')
        records_as_assembler = Record.objects.filter(assembler_worker=worker).select_related('designer', 'designer_worker', 'assembler_worker')
        
        # Объединяем все записи
        all_records = (records_as_designer | records_as_designer_worker | records_as_assembler).distinct()
        
        # Рассчитываем зарплату для каждой записи
        records_with_salary = []
        total_salary = Decimal('0')
        
        for record in all_records:
            salary = Decimal('0')
            
            # Определяем роль и рассчитываем зарплату
            role_key = None
            role_display = None
            
            if record.designer == worker:
                role_key = 'designer'
                role_display = 'Проектировщик'
                salary = calculate_worker_salary(record, worker, 'designer')
            elif record.designer_worker == worker:
                role_key = 'designer_worker'
                role_display = 'Дизайнер'
                salary = calculate_worker_salary(record, worker, 'designer_worker')
            elif record.assembler_worker == worker:
                role_key = 'assembler_worker'
                role_display = 'Сборщик'
                salary = calculate_worker_salary(record, worker, 'assembler_worker')
            
            if salary > 0 and role_key:
                # Получаем или создаем запись о выплате
                try:
                    payment = WorkerPayment.objects.get(
                        record=record,
                        worker=worker,
                        role=role_key
                    )
                    # Обновляем сумму, если она изменилась
                    if payment.amount != salary:
                        payment.amount = salary
                        payment.save(update_fields=['amount'])
                except WorkerPayment.DoesNotExist:
                    # Создаем новую запись о выплате
                    payment = WorkerPayment.objects.create(
                        record=record,
                        worker=worker,
                        role=role_key,
                        amount=salary,
                        is_paid=False
                    )
                
                # Добавляем в список все выплаты (и оплаченные, и неоплаченные)
                records_with_salary.append({
                    'record': record,
                    'salary': salary,
                    'role': role_display,
                    'role_key': role_key,
                    'contract_amount': record.contract_amount or Decimal('0'),
                    'status': record.get_status_display(),
                    'created_at': record.created_at,
                    'payment': payment,
                    'is_paid': payment.is_paid,
                })
                total_salary += salary
        
        if records_with_salary or total_salary > 0:
            # Сортируем записи: сначала неоплаченные, потом оплаченные (внутри каждой группы по дате создания - новые сначала)
            # True (оплачено) идет после False (не оплачено), поэтому сортируем по is_paid, потом по дате
            from datetime import datetime
            sorted_records = sorted(
                records_with_salary, 
                key=lambda x: (
                    x['is_paid'],  # False (не оплачено) идет первым, True (оплачено) идет вторым
                    -x['created_at'].timestamp() if isinstance(x['created_at'], datetime) else 0
                )
            )
            workers_data.append({
                'worker': worker,
                'records': sorted_records,
                'total_salary': total_salary,
                'records_count': len(records_with_salary),
            })
    
    # Сортируем по общей сумме зарплаты (по убыванию)
    workers_data.sort(key=lambda x: x['total_salary'], reverse=True)
    
    # Общая сумма всех выплат
    total_payments = sum(w['total_salary'] for w in workers_data)
    
    # Общее количество заказов (уникальных записей)
    all_record_ids = set()
    for worker_data in workers_data:
        for record_data in worker_data['records']:
            all_record_ids.add(record_data['record'].id)
    total_records_count = len(all_record_ids)
    
    # Получаем все активные (неоплаченные) выплаты
    active_payments = WorkerPayment.objects.filter(
        is_paid=False
    ).select_related(
        'record', 'worker'
    ).order_by('-created_at')
    
    # Формируем данные для активных выплат
    active_payments_data = []
    for payment in active_payments:
        active_payments_data.append({
            'payment': payment,
            'record': payment.record,
            'worker': payment.worker,
            'amount': payment.amount,
            'role': payment.get_role_display(),
            'created_at': payment.created_at,
        })
    
    # Общая сумма активных выплат
    total_active_payments = sum(p['amount'] for p in active_payments_data)
    total_active_count = len(active_payments_data)

    # Группируем активные выплаты по заказам для аккордеона
    active_orders_map = {}
    for payment_data in active_payments_data:
        record = payment_data['record']
        if record.id not in active_orders_map:
            active_orders_map[record.id] = {
                'record': record,
                'total_amount': Decimal('0'),
                'payments': []
            }
        active_orders_map[record.id]['total_amount'] += payment_data['amount']
        active_orders_map[record.id]['payments'].append(payment_data)

    active_orders = sorted(
        active_orders_map.values(),
        key=lambda x: x['record'].created_at,
        reverse=True
    )

    # Группируем выплаты по заказам для отображения сводки по каждому заказу
    order_payments_map = {}
    payments_qs = WorkerPayment.objects.select_related('record', 'worker').order_by('-record__created_at')

    for payment in payments_qs:
        record = payment.record
        if record.id not in order_payments_map:
            order_payments_map[record.id] = {
                'record': record,
                'total_amount': Decimal('0'),
                'paid_amount': Decimal('0'),
                'unpaid_amount': Decimal('0'),
                'payments': []
            }
        order_entry = order_payments_map[record.id]
        order_entry['total_amount'] += payment.amount
        if payment.is_paid:
            order_entry['paid_amount'] += payment.amount
        else:
            order_entry['unpaid_amount'] += payment.amount

        order_entry['payments'].append({
            'payment': payment,
            'worker': payment.worker,
            'role': payment.get_role_display(),
            'amount': payment.amount,
            'is_paid': payment.is_paid,
            'paid_at': payment.paid_at,
            'created_at': payment.created_at,
        })

    orders_data = sorted(
        order_payments_map.values(),
        key=lambda x: x['record'].created_at,
        reverse=True
    )
    total_orders_amount = sum(item['total_amount'] for item in orders_data)
    
    return render(request, 'payments.html', {
        'workers_data': workers_data,
        'total_payments': total_payments,
        'workers_count': len(workers_data),
        'total_records_count': total_records_count,
        'active_payments': active_payments_data,
        'total_active_payments': total_active_payments,
        'active_payments_count': total_active_count,
        'active_orders': active_orders,
        'active_orders_count': len(active_orders),
        'orders_data': orders_data,
        'orders_count': len(orders_data),
        'total_orders_amount': total_orders_amount,
    })


def calculate_worker_salary(record, worker, role):
    """Рассчитывает зарплату работника для конкретной записи"""
    salary = Decimal('0')
    
    try:
        method_name = worker.method.name.lower() if worker.method else ''
        
        # Проектировщик
        if role == 'designer':
            if 'процент' in method_name and worker.percentage and record.contract_amount:
                salary = (record.contract_amount * worker.percentage) / 100
            elif 'погон' in method_name:
                rate = Decimal(str(worker.rate_per_square_meter)) if worker.rate_per_square_meter else Decimal('0')
                meters = Decimal(str(record.designer_manual_salary)) if record.designer_manual_salary is not None else Decimal('0')
                salary = rate * meters if rate > 0 and meters > 0 else Decimal('0')
            elif ('м²' in method_name or 'метр' in method_name) and worker.rate_per_square_meter:
                try:
                    sum_area = Decimal(str(get_record_files_area(record)))
                    if sum_area > 0:
                        salary = (worker.rate_per_square_meter or Decimal('0')) * sum_area
                except Exception:
                    salary = Decimal('0')
        
        # Дизайнер
        elif role == 'designer_worker':
            if ('процент' in method_name or (not worker.method and worker.percentage)) and worker.percentage and record.contract_amount:
                salary = (record.contract_amount * worker.percentage) / 100
            elif ('м²' in method_name or 'метр' in method_name or (not worker.method and worker.rate_per_square_meter)) and worker.rate_per_square_meter:
                try:
                    sum_area = Decimal(str(get_record_files_area(record)))
                    salary = (worker.rate_per_square_meter or Decimal('0')) * sum_area
                except Exception:
                    salary = Decimal('0')
            elif 'погон' in method_name and record.designer_worker_manual_salary is not None:
                meters = Decimal(str(record.designer_worker_manual_salary))
                rate = worker.rate_per_square_meter or Decimal('0')
                salary = rate * meters if rate > 0 and meters > 0 else Decimal('0')
        
        # Сборщик
        elif role == 'assembler_worker':
            if ('процент' in method_name or (not worker.method and worker.percentage)) and worker.percentage and record.contract_amount:
                salary = (record.contract_amount * worker.percentage) / 100
            elif ('м²' in method_name or 'метр' in method_name or (not worker.method and worker.rate_per_square_meter)) and worker.rate_per_square_meter:
                try:
                    sum_area = Decimal(str(get_record_files_area(record)))
                    salary = (worker.rate_per_square_meter or Decimal('0')) * sum_area
                except Exception:
                    salary = Decimal('0')
            elif 'погон' in method_name and record.assembler_worker_manual_salary is not None:
                meters = Decimal(str(record.assembler_worker_manual_salary))
                rate = worker.rate_per_square_meter or Decimal('0')
                salary = rate * meters if rate > 0 and meters > 0 else Decimal('0')
    
    except Exception as e:
        salary = Decimal('0')
    
    return salary


@login_required
def mark_payment_paid(request, payment_id):
    """Отметить выплату как оплаченную"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для отметки выплат')
        return redirect('payments_page')
    
    payment = get_object_or_404(WorkerPayment, id=payment_id)
    
    if request.method == 'POST':
        payment.is_paid = True
        payment.paid_at = timezone.now()
        payment.save(update_fields=['is_paid', 'paid_at'])
        messages.success(request, f'Выплата работнику {payment.worker.name} {payment.worker.surname} отмечена как оплаченная')
    
    return redirect('payments_page')


@login_required
def mark_payment_unpaid(request, payment_id):
    """Отметить выплату как неоплаченную"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для отметки выплат')
        return redirect('payments_page')
    
    payment = get_object_or_404(WorkerPayment, id=payment_id)
    
    if request.method == 'POST':
        payment.is_paid = False
        payment.paid_at = None
        payment.save(update_fields=['is_paid', 'paid_at'])
        messages.success(request, f'Выплата работнику {payment.worker.name} {payment.worker.surname} отмечена как неоплаченная')
    
    return redirect('payments_page')

