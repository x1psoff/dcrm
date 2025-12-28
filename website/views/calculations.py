"""Функции для расчетов зарплат и моржи"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from ..models import Record, RecordProduct
from ..utils.csv_cache import get_record_files_area


def calculate_record_total_components(record):
    """Вычисляет общую стоимость комплектующих для записи"""
    total_products = 0
    for record_product in record.recordproduct_set.all():
        if record_product.custom_price:
            total_products += float(record_product.custom_price) * record_product.quantity
        else:
            product_price = record_product.product.our_price or 0
            total_products += float(product_price) * record_product.quantity
    
    # Плиты больше не используются
    return total_products


def calculate_record_total_expenses(record):
    """Вычисляет общую стоимость непланируемых расходов для записи"""
    return sum(float(expense.price) for expense in record.unplanned_expenses.all())


def calculate_record_margin(record):
    """Вычисляет моржу для записи"""
    total_components = calculate_record_total_components(record)
    total_expenses = calculate_record_total_expenses(record)
    
    # Зарплата проектировщика
    designer_salary = Decimal('0')
    if record.designer:
        d = record.designer
        method_name = d.method.name.lower() if d.method else ''
        
        if 'процент' in method_name and d.percentage and record.contract_amount:
            try:
                designer_salary = (record.contract_amount * d.percentage) / 100
            except Exception:
                designer_salary = Decimal('0')
        elif 'погон' in method_name:
            try:
                rate = Decimal(str(d.rate_per_square_meter)) if d.rate_per_square_meter else Decimal('0')
                meters = Decimal(str(record.designer_manual_salary)) if record.designer_manual_salary is not None else Decimal('0')
                designer_salary = rate * meters if rate > 0 else Decimal('0')
            except Exception:
                designer_salary = Decimal('0')
        elif ('м²' in method_name or 'метр' in method_name) and d.rate_per_square_meter:
            try:
                sum_area = Decimal(str(get_record_files_area(record)))
                if sum_area > 0:
                    designer_salary = (d.rate_per_square_meter or Decimal('0')) * sum_area
            except Exception:
                designer_salary = Decimal('0')
    
    # Зарплата дизайнера
    designer_worker_salary = Decimal('0')
    if record.designer_worker:
        dw = record.designer_worker
        method_name = dw.method.name.lower() if dw.method else ''
        
        if ('процент' in method_name or (not dw.method and dw.percentage)) and dw.percentage and record.contract_amount:
            try:
                designer_worker_salary = (record.contract_amount * dw.percentage) / 100
            except Exception:
                designer_worker_salary = Decimal('0')
        elif 'погон' in method_name and record.designer_worker_manual_salary is not None:
            try:
                meters = Decimal(str(record.designer_worker_manual_salary))
                rate = dw.rate_per_square_meter or Decimal('0')
                designer_worker_salary = rate * meters
            except Exception:
                designer_worker_salary = Decimal('0')
        elif ('м²' in method_name or 'метр' in method_name or (not dw.method and dw.rate_per_square_meter)) and dw.rate_per_square_meter:
            try:
                sum_area = Decimal(str(get_record_files_area(record)))
                designer_worker_salary = (dw.rate_per_square_meter or Decimal('0')) * sum_area
            except Exception:
                designer_worker_salary = Decimal('0')
    
    # Зарплата сборщика
    assembler_worker_salary = Decimal('0')
    if record.assembler_worker:
        aw = record.assembler_worker
        method_name = aw.method.name.lower() if aw.method else ''
        
        if ('процент' in method_name or (not aw.method and aw.percentage)) and aw.percentage and record.contract_amount:
            try:
                assembler_worker_salary = (record.contract_amount * aw.percentage) / 100
            except Exception:
                assembler_worker_salary = Decimal('0')
        elif 'погон' in method_name and record.assembler_worker_manual_salary is not None:
            try:
                meters = Decimal(str(record.assembler_worker_manual_salary))
                rate = aw.rate_per_square_meter or Decimal('0')
                assembler_worker_salary = rate * meters
            except Exception:
                assembler_worker_salary = Decimal('0')
        elif ('м²' in method_name or 'метр' in method_name or (not aw.method and aw.rate_per_square_meter)) and aw.rate_per_square_meter:
            try:
                sum_area = Decimal(str(get_record_files_area(record)))
                assembler_worker_salary = (aw.rate_per_square_meter or Decimal('0')) * sum_area
            except Exception:
                assembler_worker_salary = Decimal('0')
    
    # Дополнительные расходы
    delivery_price_dec = Decimal(str(record.delivery_price)) if record.delivery_price else Decimal('0')
    workshop_price_dec = Decimal(str(record.workshop_price)) if record.workshop_price else Decimal('0')
    additional_costs = delivery_price_dec + workshop_price_dec
    
    # Общая сумма затрат
    total_components_dec = Decimal(str(total_components)) if total_components else Decimal('0')
    total_expenses_dec = Decimal(str(total_expenses)) if total_expenses else Decimal('0')
    designer_salary_dec = Decimal(str(designer_salary)) if designer_salary else Decimal('0')
    designer_worker_salary_dec = Decimal(str(designer_worker_salary)) if designer_worker_salary else Decimal('0')
    assembler_worker_salary_dec = Decimal(str(assembler_worker_salary)) if assembler_worker_salary else Decimal('0')
    
    total_amount = total_components_dec + total_expenses_dec + designer_salary_dec + designer_worker_salary_dec + assembler_worker_salary_dec + additional_costs
    
    # Общая моржа
    margin_total = Decimal('0')
    if record.contract_amount:
        try:
            contract_amount_dec = Decimal(str(record.contract_amount))
            margin_total = contract_amount_dec - total_amount
        except (ValueError, TypeError, Exception):
            margin_total = Decimal('0')
    
    # Учет индивидуальных расходов по людям
    unplanned_spent = {
        'Юра': sum(e.price for e in record.unplanned_expenses.filter(spent_by='Юра')),
        'Олег': sum(e.price for e in record.unplanned_expenses.filter(spent_by='Олег')),
    }
    
    buyer_product_spent = {'Юра': Decimal('0'), 'Олег': Decimal('0')}
    for rp in record.recordproduct_set.all().select_related('product'):
        unit_price = rp.custom_price if rp.custom_price is not None else rp.product.our_price
        try:
            line_total = Decimal(str(unit_price)) * Decimal(rp.quantity)
        except Exception:
            line_total = Decimal('0')
        if rp.buyer in buyer_product_spent:
            buyer_product_spent[rp.buyer] += line_total
    
    spent_by_totals = {
        'Юра': Decimal(str(unplanned_spent['Юра'])) + buyer_product_spent['Юра'],
        'Олег': Decimal(str(unplanned_spent['Олег'])) + buyer_product_spent['Олег'],
    }
    
    # Распределение моржи
    recipients = []
    if record.margin_yura:
        recipients.append('Юра')
    if record.margin_oleg:
        recipients.append('Олег')
    if not recipients:
        recipients = ['Юра', 'Олег']
    
    per_head = (margin_total / len(recipients)) if recipients else Decimal('0')
    
    margin_distribution = {}
    if 'Юра' in recipients:
        margin_distribution['Юра'] = per_head - spent_by_totals.get('Олег', Decimal('0'))
    if 'Олег' in recipients:
        margin_distribution['Олег'] = per_head - spent_by_totals.get('Юра', Decimal('0'))
    
    return {
        'margin_total': float(margin_total),
        'margin_yura': float(margin_distribution.get('Юра', Decimal('0'))),
        'margin_oleg': float(margin_distribution.get('Олег', Decimal('0'))),
        'total_amount': float(total_amount),
    }


@login_required
def set_designer_manual_salary(request, pk):
    """Установка погонных метров проектировщика - только для администраторов"""
    record = get_object_or_404(Record, id=pk)
    
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для изменения погонных метров')
        return redirect('record_detail', pk=pk)
    
    if request.method == 'POST':
        value = request.POST.get('designer_manual_salary', '').strip()
        try:
            if value and value != '':
                decimal_value = Decimal(value)
                if decimal_value < 0:
                    messages.error(request, 'Погонные метры не могут быть отрицательными')
                    return redirect('record_detail', pk=pk)
                record.designer_manual_salary = decimal_value
            else:
                record.designer_manual_salary = None
            record.save(update_fields=['designer_manual_salary'])
            messages.success(request, f'Погонные метры проектировщика сохранены: {record.designer_manual_salary or 0} м')
        except (ValueError, InvalidOperation, Exception) as e:
            messages.error(request, f'Неверное значение погонных метров: {str(e)}')
    return redirect('record_detail', pk=pk)


@login_required
def set_designer_worker_manual_salary(request, pk):
    """Установка погонных метров дизайнера - только для администраторов"""
    record = get_object_or_404(Record, id=pk)
    
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для изменения погонных метров')
        return redirect('record_detail', pk=pk)
    
    if request.method == 'POST':
        value = request.POST.get('designer_worker_manual_salary', '').strip()
        try:
            if value:
                record.designer_worker_manual_salary = Decimal(value)
            else:
                record.designer_worker_manual_salary = None
            record.save(update_fields=['designer_worker_manual_salary'])
            messages.success(request, 'Погонные метры дизайнера сохранены')
        except (ValueError, InvalidOperation, Exception) as e:
            messages.error(request, f'Неверное значение погонных метров: {str(e)}')
    return redirect('record_detail', pk=pk)


@login_required
def set_assembler_worker_manual_salary(request, pk):
    """Установка погонных метров сборщика - только для администраторов"""
    record = get_object_or_404(Record, id=pk)
    
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для изменения погонных метров')
        return redirect('record_detail', pk=pk)
    
    if request.method == 'POST':
        value = request.POST.get('assembler_worker_manual_salary', '').strip()
        try:
            if value:
                record.assembler_worker_manual_salary = Decimal(value)
            else:
                record.assembler_worker_manual_salary = None
            record.save(update_fields=['assembler_worker_manual_salary'])
            messages.success(request, 'Погонные метры сборщика сохранены')
        except (ValueError, InvalidOperation, Exception) as e:
            messages.error(request, f'Неверное значение погонных метров: {str(e)}')
    return redirect('record_detail', pk=pk)

