"""Функции для работы с записями"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from decimal import Decimal, InvalidOperation
import os
import logging
from django.conf import settings
from ..models import Record, RecordProduct, UploadedFile, Category, Designer, Profile
from ..forms import AddRecordForm, UpdateRecordForm
from ..utils.csv_cache import get_record_files_area

logger = logging.getLogger(__name__)


def customer_record(request, pk):
    if request.user.is_authenticated:
        customer_record = Record.objects.get(id=pk)
        return render(request, 'record.html', {'customer_record': customer_record})
    else:
        messages.success(request, "You Must Be Logged In To View That Page...")
        return redirect('home')


def delete_record(request, pk):
    """Удаление записи - только для администраторов"""
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        messages.error(request, 'У вас нет прав для удаления заказа')
        return redirect('record_detail', pk=pk)
    
    delete_it = Record.objects.get(id=pk)
    delete_it.delete()
    messages.success(request, "Record Deleted Successfully...")
    return redirect('home')


def add_record(request):
    from ..telegram_bot.notifications import notify_workers_about_record
    
    if request.method == 'POST':
        form = AddRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save()
            if 'file' in request.FILES:
                UploadedFile.objects.create(record=record, file=request.FILES['file'])
            
            # Отправляем уведомления работникам о новом заказе
            try:
                logger.info(f"Отправка уведомления о новом заказе #{record.id}")
                notify_workers_about_record(record, message_type='created')
                logger.info(f"Уведомления о новом заказе #{record.id} отправлены")
            except Exception as e:
                # Не прерываем выполнение, если уведомление не отправилось
                logger.error(f"Ошибка отправки уведомления о новом заказе #{record.id}: {e}", exc_info=True)
            
            messages.success(request, "Запись успешно добавлена!")
            return redirect('home')
    else:
        form = AddRecordForm()
    return render(request, 'add_record.html', {'form': form})


def update_record(request, pk):
    current_record = get_object_or_404(Record, id=pk)
    
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        messages.error(request, 'У вас нет прав для редактирования заказа')
        return redirect('record_detail', pk=pk)
    
    if request.method == 'POST':
        form = UpdateRecordForm(request.POST, request.FILES, instance=current_record)
        if form.is_valid():
            record = form.save()
            if 'file' in request.FILES:
                UploadedFile.objects.create(record=record, file=request.FILES['file'])
            messages.success(request, "Запись успешно обновлена!")
            return redirect('record_detail', pk=record.id)
    else:
        form = UpdateRecordForm(instance=current_record)
    
    all_workers = Designer.objects.all()
    
    return render(request, 'update_record.html', {
        'form': form,
        'current_record': current_record,
        'all_workers': all_workers
    })


@login_required
def set_margin_flags(request, pk):
    record = get_object_or_404(Record, id=pk)
    if request.method == 'POST':
        record.margin_yura = bool(request.POST.get('margin_yura'))
        record.margin_oleg = bool(request.POST.get('margin_oleg'))
        record.save(update_fields=['margin_yura', 'margin_oleg'])
        messages.success(request, 'Флаги распределения моржи сохранены')
    return redirect('record_detail', pk=pk)


@login_required
def update_record_status(request, pk):
    """Изменение статуса записи - только для администраторов"""
    from ..telegram_bot.notifications import notify_workers_about_record
    
    # Получаем запись с предзагрузкой связанных объектов
    record = get_object_or_404(
        Record.objects.select_related('designer', 'designer_worker', 'assembler_worker'),
        id=pk
    )
    
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для изменения статуса заказа')
        return redirect('record_detail', pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Record.STATUS_CHOICES):
            old_status = record.status
            record.status = new_status
            record.save(update_fields=['status'])
            
            # Отправляем уведомления работникам об изменении статуса
            if old_status != new_status:
                try:
                    logger.info(f"Отправка уведомления об изменении статуса заказа #{record.id} с '{old_status}' на '{new_status}'")
                    notify_workers_about_record(record, message_type='status_changed')
                    logger.info(f"Уведомления об изменении статуса заказа #{record.id} отправлены")
                except Exception as e:
                    # Не прерываем выполнение, если уведомление не отправилось
                    logger.error(f"Ошибка отправки уведомления об изменении статуса заказа #{record.id}: {e}", exc_info=True)
            
            messages.success(request, 'Статус заказа обновлен!')
        else:
            messages.error(request, 'Неверный статус')
    return redirect('record_detail', pk=pk)


def record_detail(request, pk):
    """Детальная информация о записи с расчетами зарплат и моржи"""
    customer_record = get_object_or_404(Record, id=pk)
    
    # Проверка прав доступа
    user_role = None
    user_designer = None
    user_payment_method = None
    
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            user_role = 'admin'
        else:
            try:
                profile = request.user.profile
                if profile and profile.designer:
                    user_designer = profile.designer
                    user_role = profile.designer.profession.name if profile.designer.profession else None
                    
                    if not (customer_record.designer == user_designer or 
                            customer_record.designer_worker == user_designer or 
                            customer_record.assembler_worker == user_designer):
                        return HttpResponseForbidden("У вас нет доступа к этой записи.")
                    
                    if user_role == 'дизайнер' and user_designer.method:
                        user_payment_method = user_designer.method.name.lower()
            except Profile.DoesNotExist:
                return HttpResponseForbidden("У вас нет доступа к этой записи.")
    else:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Загружаем категории - можно кэшировать, но пока просто оптимизируем запрос
    categories = Category.objects.all()

    product_filter = request.GET.get('category', None)
    products = customer_record.products.select_related('category').prefetch_related('recordproduct_set').all()
    if product_filter:
        products = products.filter(category__name=product_filter)

    # Расчет сумм - используем уже загруженные данные
    rps = RecordProduct.objects.filter(record=customer_record).select_related('product', 'product__category')
    rp_map = {rp.product_id: rp for rp in rps}
    total_products = sum(
        (rp.custom_price if rp.custom_price is not None else rp.product.our_price) * rp.quantity
        for rp in rps
    )

    # Плиты больше не используются
    record_plitas = []
    plitas_total = 0
    try:
        total_components = total_products + plitas_total
    except Exception:
        total_components = total_products

    # Единая таблица компонентов
    unified_components = []
    
    for product in products:
        category_name = product.category.name if product.category else 'Без категории'
        rp = rp_map.get(product.id)
        unit_price = (rp.custom_price if (rp and rp.custom_price is not None) else product.our_price)
        quantity = rp.quantity if rp else 1
        try:
            line_total = unit_price * quantity
        except Exception:
            line_total = unit_price
        
        component_type = 'Другие'
        if 'петл' in category_name.lower():
            component_type = 'Петли'
        elif 'направля' in category_name.lower():
            component_type = 'Направляющие'
        
        unified_components.append({
            'type': component_type,
            'name': product.name,
            'category': category_name,
            'specifications': {
                'hinge_angle': product.hinge_angle,
                'hinge_closing_type': product.hinge_closing_type,
                'runner_size': product.runner_size,
                'response_type': product.response_type,
                'mounting_type': product.mounting_type,
            },
            'unit_price': unit_price,
            'quantity': quantity,
            'line_total': line_total,
            'buyer': rp.buyer if rp else 'Юра',
            'is_product': True,
            'product_id': product.id
        })
    
    
    unified_components.sort(key=lambda x: (x['type'], x['name']))
    
    # Группировка по категориям
    products_by_category = {}
    category_counts = {}
    for product in products:
        category_name = product.category.name if product.category else 'Без категории'
        rp = rp_map.get(product.id)
        unit_price = (rp.custom_price if (rp and rp.custom_price is not None) else product.our_price)
        quantity = rp.quantity if rp else 1
        try:
            line_total = unit_price * quantity
        except Exception:
            line_total = unit_price
        products_by_category.setdefault(category_name, []).append({
            'product': product,
            'rp': rp,
            'unit_price': unit_price,
            'quantity': quantity,
            'line_total': line_total,
        })
        category_counts[category_name] = category_counts.get(category_name, 0) + 1

    products_by_category = dict(sorted(products_by_category.items(), key=lambda kv: kv[0].lower()))
    category_counts = dict(sorted(category_counts.items(), key=lambda kv: kv[0].lower()))

    hinge_count = sum(len(items) for name, items in products_by_category.items() if 'петл' in name.lower())
    runner_count = sum(len(items) for name, items in products_by_category.items() if 'направля' in name.lower())
    plita_count = len(record_plitas)
    # Загружаем все расходы одним запросом
    all_expenses = list(customer_record.unplanned_expenses.all())
    total_expenses = sum(expense.price for expense in all_expenses)
    
    expenses_yura = [e for e in all_expenses if e.spent_by == 'Юра']
    expenses_oleg = [e for e in all_expenses if e.spent_by == 'Олег']
    total_expenses_yura = sum(expense.price for expense in expenses_yura)
    total_expenses_oleg = sum(expense.price for expense in expenses_oleg)

    # Расчет зарплаты проектировщика
    designer_salary = 0
    designer_info = ''
    if customer_record.designer:
        d = customer_record.designer
        method_name = d.method.name.lower() if d.method else ''
        
        if 'процент' in method_name and d.percentage and customer_record.contract_amount:
            try:
                designer_salary = (customer_record.contract_amount * d.percentage) / 100
                designer_info = f"{d.name} {d.surname} — {d.percentage}% от договора"
            except Exception:
                designer_salary = 0
        elif 'погон' in method_name:
            try:
                if d.rate_per_square_meter is not None:
                    rate = Decimal(str(d.rate_per_square_meter))
                else:
                    rate = Decimal('0')
                
                if customer_record.designer_manual_salary is not None:
                    meters = Decimal(str(customer_record.designer_manual_salary))
                else:
                    meters = Decimal('0')
                
                if rate > 0:
                    designer_salary = float(rate * meters)
                    if meters > 0:
                        designer_info = f"{d.name} {d.surname} — {rate} ₽/м × {meters} м"
                    else:
                        designer_info = f"{d.name} {d.surname} — {rate} ₽/м × {meters} м (не указаны метры)"
                else:
                    designer_salary = 0
                    designer_info = f"{d.name} {d.surname} — погонный метр (ставка не указана или равна 0)"
            except (ValueError, InvalidOperation, TypeError, Exception) as e:
                designer_salary = 0
                designer_info = f"{d.name} {d.surname} — погонный метр (ошибка расчета: {str(e)})"
        elif ('м²' in method_name or 'метр' in method_name) and d.rate_per_square_meter:
            try:
                sum_area = get_record_files_area(customer_record)
                if sum_area > 0:
                    designer_salary = float((d.rate_per_square_meter or 0) * sum_area)
                    designer_info = f"{d.name} {d.surname} — {d.rate_per_square_meter} ₽/м² ({sum_area:.2f} м²)"
                else:
                    designer_salary = 0
                    designer_info = f"{d.name} {d.surname} — м² (нет файлов или данных)"
            except Exception:
                designer_salary = 0
                designer_info = f"{d.name} {d.surname} — м² (ошибка расчета)"

    # Расчет зарплаты дизайнера
    designer_worker_salary = 0
    designer_worker_info = ''
    if customer_record.designer_worker:
        dw = customer_record.designer_worker
        method_name = dw.method.name.lower() if dw.method else ''
        
        if ('процент' in method_name or (not dw.method and dw.percentage)) and dw.percentage and customer_record.contract_amount:
            try:
                designer_worker_salary = (customer_record.contract_amount * dw.percentage) / 100
                designer_worker_info = f"{dw.name} {dw.surname} — {dw.percentage}% от договора"
            except Exception:
                designer_worker_salary = 0
        elif ('м²' in method_name or 'метр' in method_name or (not dw.method and dw.rate_per_square_meter)) and dw.rate_per_square_meter:
            try:
                sum_area = get_record_files_area(customer_record)
                designer_worker_salary = (dw.rate_per_square_meter or 0) * sum_area
                designer_worker_info = f"{dw.name} {dw.surname} — {dw.rate_per_square_meter} ₽/м² ({sum_area:.2f} м²)"
            except Exception:
                designer_worker_salary = 0
        elif 'погон' in method_name and customer_record.designer_worker_manual_salary is not None:
            try:
                meters = Decimal(str(customer_record.designer_worker_manual_salary))
            except Exception:
                meters = Decimal('0')
            rate = dw.rate_per_square_meter or Decimal('0')
            designer_worker_salary = rate * meters
            designer_worker_info = f"{dw.name} {dw.surname} — {rate} ₽/м × {meters} м"

    # Расчет зарплаты сборщика
    assembler_worker_salary = 0
    assembler_worker_info = ''
    if customer_record.assembler_worker:
        aw = customer_record.assembler_worker
        method_name = aw.method.name.lower() if aw.method else ''
        
        if ('процент' in method_name or (not aw.method and aw.percentage)) and aw.percentage and customer_record.contract_amount:
            try:
                assembler_worker_salary = (customer_record.contract_amount * aw.percentage) / 100
                assembler_worker_info = f"{aw.name} {aw.surname} — {aw.percentage}% от договора"
            except Exception:
                assembler_worker_salary = 0
        elif ('м²' in method_name or 'метр' in method_name or (not aw.method and aw.rate_per_square_meter)) and aw.rate_per_square_meter:
            try:
                sum_area = get_record_files_area(customer_record)
                assembler_worker_salary = (aw.rate_per_square_meter or 0) * sum_area
                assembler_worker_info = f"{aw.name} {aw.surname} — {aw.rate_per_square_meter} ₽/м² ({sum_area:.2f} м²)"
            except Exception:
                assembler_worker_salary = 0
        elif 'погон' in method_name and customer_record.assembler_worker_manual_salary is not None:
            try:
                meters = Decimal(str(customer_record.assembler_worker_manual_salary))
            except Exception:
                meters = Decimal('0')
            rate = aw.rate_per_square_meter or Decimal('0')
            assembler_worker_salary = rate * meters
            assembler_worker_info = f"{aw.name} {aw.surname} — {rate} ₽/м × {meters} м"

    # Дополнительные расходы
    delivery_price_dec = Decimal(str(customer_record.delivery_price)) if customer_record.delivery_price else Decimal('0')
    workshop_price_dec = Decimal(str(customer_record.workshop_price)) if customer_record.workshop_price else Decimal('0')
    additional_costs = delivery_price_dec + workshop_price_dec

    total_components_dec = Decimal(str(total_components)) if total_components else Decimal('0')
    total_expenses_dec = Decimal(str(total_expenses)) if total_expenses else Decimal('0')
    designer_salary_dec = Decimal(str(designer_salary)) if designer_salary else Decimal('0')
    designer_worker_salary_dec = Decimal(str(designer_worker_salary)) if designer_worker_salary else Decimal('0')
    assembler_worker_salary_dec = Decimal(str(assembler_worker_salary)) if assembler_worker_salary else Decimal('0')
    
    total_amount = total_components_dec + total_expenses_dec + designer_salary_dec + designer_worker_salary_dec + assembler_worker_salary_dec + additional_costs

    margin_total = Decimal('0')
    if customer_record.contract_amount:
        try:
            contract_amount_dec = Decimal(str(customer_record.contract_amount))
            margin_total = contract_amount_dec - total_amount
        except (ValueError, TypeError, Exception):
            margin_total = Decimal('0')

    unplanned_spent = {
        'Юра': sum(e.price for e in customer_record.unplanned_expenses.filter(spent_by='Юра')),
        'Олег': sum(e.price for e in customer_record.unplanned_expenses.filter(spent_by='Олег')),
    }
    
    buyer_product_spent = {'Юра': Decimal('0'), 'Олег': Decimal('0')}
    for rp in RecordProduct.objects.filter(record=customer_record).select_related('product'):
        unit_price = rp.custom_price if rp.custom_price is not None else rp.product.our_price
        try:
            line_total = Decimal(unit_price) * Decimal(rp.quantity)
        except Exception:
            line_total = Decimal('0')
        if rp.buyer in buyer_product_spent:
            buyer_product_spent[rp.buyer] += line_total

    spent_by_totals = {
        'Юра': unplanned_spent['Юра'] + buyer_product_spent['Юра'],
        'Олег': unplanned_spent['Олег'] + buyer_product_spent['Олег'],
    }

    recipients = []
    if customer_record.margin_yura:
        recipients.append('Юра')
    if customer_record.margin_oleg:
        recipients.append('Олег')
    if not recipients:
        recipients = ['Юра', 'Олег']

    per_head = (margin_total / len(recipients)) if recipients else Decimal('0')
    margin_distribution = {}
    if 'Юра' in recipients:
        margin_distribution['Юра'] = per_head - Decimal(spent_by_totals.get('Олег', 0))
    if 'Олег' in recipients:
        margin_distribution['Олег'] = per_head - Decimal(spent_by_totals.get('Юра', 0))

    margin_yura_value = margin_distribution.get('Юра', Decimal('0'))
    margin_oleg_value = margin_distribution.get('Олег', Decimal('0'))
    spent_yura = spent_by_totals.get('Юра', Decimal('0'))
    spent_oleg = spent_by_totals.get('Олег', Decimal('0'))

    # Определяем права доступа
    show_all_info = (user_role == 'admin')
    
    if user_role == 'admin':
        show_components = show_expenses = show_margin = show_files = True
        show_contract_amount = show_advance = True
        show_designer_salary = show_designer_worker_salary = show_assembler_worker_salary = True
        show_customer_data = show_calculation = show_workers_info = True
    elif user_role == 'дизайнер':
        show_components = show_expenses = show_margin = False
        show_files = show_customer_data = show_calculation = show_workers_info = True
        show_contract_amount = show_advance = True
        if user_payment_method and 'погон' in user_payment_method:
            show_contract_amount = show_advance = False
        show_designer_worker_salary = True
        show_designer_salary = show_assembler_worker_salary = False
    elif user_role == 'сборщики':
        show_components = show_files = show_customer_data = show_calculation = show_workers_info = True
        show_expenses = show_margin = False
        show_contract_amount = show_advance = True
        if customer_record.designer_worker and customer_record.designer_worker.method:
            method_name = customer_record.designer_worker.method.name.lower()
            if 'процент' not in method_name:
                show_contract_amount = show_advance = False
        show_assembler_worker_salary = True
        show_designer_salary = show_designer_worker_salary = False
    elif user_role == 'проектировщик':
        show_components = show_expenses = show_margin = show_customer_data = False
        show_files = show_calculation = show_workers_info = True
        show_designer_salary = True
        show_designer_worker_salary = show_assembler_worker_salary = False
        if customer_record.designer == user_designer and customer_record.designer.method:
            designer_payment_method = customer_record.designer.method.name.lower()
            if 'погон' in designer_payment_method:
                show_contract_amount = show_advance = False
            else:
                show_contract_amount = show_advance = True
        else:
            show_contract_amount = show_advance = True
    else:
        show_components = show_expenses = show_margin = show_files = True
        show_contract_amount = show_advance = True
        show_designer_salary = show_designer_worker_salary = show_assembler_worker_salary = True
        show_customer_data = show_calculation = show_workers_info = True
    
    workers_on_project = []
    if customer_record.designer:
        workers_on_project.append({
            'name': customer_record.designer.name,
            'surname': customer_record.designer.surname,
            'profession': customer_record.designer.profession.name if customer_record.designer.profession else None,
            'role': 'designer'
        })
    if customer_record.designer_worker:
        workers_on_project.append({
            'name': customer_record.designer_worker.name,
            'surname': customer_record.designer_worker.surname,
            'profession': customer_record.designer_worker.profession.name if customer_record.designer_worker.profession else None,
            'role': 'designer_worker'
        })
    if customer_record.assembler_worker:
        workers_on_project.append({
            'name': customer_record.assembler_worker.name,
            'surname': customer_record.assembler_worker.surname,
            'profession': customer_record.assembler_worker.profession.name if customer_record.assembler_worker.profession else None,
            'role': 'assembler_worker'
        })

    return render(request, 'record.html', {
        'customer_record': customer_record,
        'categories': categories,
        'products': products,
        'products_by_category': products_by_category,
        'category_counts': category_counts,
        'record_plitas': record_plitas,
        'unified_components': unified_components,
        'hinge_count': hinge_count,
        'runner_count': runner_count,
        'plita_count': plita_count,
        'total_products': total_products,
        'plitas_total': plitas_total,
        'total_components': total_components,
        'total_expenses': total_expenses,
        'expenses_yura': expenses_yura,
        'expenses_oleg': expenses_oleg,
        'total_expenses_yura': total_expenses_yura,
        'total_expenses_oleg': total_expenses_oleg,
        'designer_salary': designer_salary,
        'designer_info': designer_info,
        'designer_worker_salary': designer_worker_salary,
        'designer_worker_info': designer_worker_info,
        'assembler_worker_salary': assembler_worker_salary,
        'assembler_worker_info': assembler_worker_info,
        'delivery_price': customer_record.delivery_price or 0,
        'workshop_price': customer_record.workshop_price or 0,
        'total_amount': total_amount,
        'margin_total': margin_total,
        'margin_distribution': margin_distribution,
        'margin_yura_value': margin_yura_value,
        'margin_oleg_value': margin_oleg_value,
        'spent_yura': spent_yura,
        'spent_oleg': spent_oleg,
        'user_role': user_role,
        'user_designer': user_designer,
        'user_payment_method': user_payment_method,
        'show_all_info': show_all_info,
        'show_components': show_components,
        'show_expenses': show_expenses,
        'show_margin': show_margin,
        'show_files': show_files,
        'show_contract_amount': show_contract_amount,
        'show_advance': show_advance,
        'show_designer_salary': show_designer_salary,
        'show_designer_worker_salary': show_designer_worker_salary,
        'show_assembler_worker_salary': show_assembler_worker_salary,
        'show_customer_data': show_customer_data,
        'show_calculation': show_calculation,
        'show_workers_info': show_workers_info,
        'workers_on_project': workers_on_project,
    })

