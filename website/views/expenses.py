"""Функции для работы с непланируемыми расходами"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import UnplannedExpense, Record
from ..forms import UnplannedExpenseForm


@login_required
def unplanned_expenses_list(request):
    """Список всех непланируемых расходов"""
    expenses = UnplannedExpense.objects.all()
    total = sum(expense.price for expense in expenses)

    return render(request, 'unplanned_expenses/list.html', {
        'expenses': expenses,
        'total': total,
        'form': UnplannedExpenseForm()  # Форма для добавления новых расходов
    })


@login_required
def add_unplanned_expense(request, pk):
    """Добавление непланируемого расхода к записи - только для администраторов"""
    record = get_object_or_404(Record, id=pk)
    
    # Проверка прав доступа - только администраторы могут добавлять непланируемые расходы
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для добавления непланируемых расходов')
        return redirect('record_detail', pk=pk)

    if request.method == 'POST':
        item = request.POST.get('item')
        price = request.POST.get('price')
        spent_by = request.POST.get('spent_by', 'Юра')  # По умолчанию Юра

        if item and price:
            UnplannedExpense.objects.create(
                record=record,
                item=item,
                price=price,
                spent_by=spent_by
            )
            messages.success(request, "Расход успешно добавлен!")
        else:
            messages.error(request, "Пожалуйста, заполните все обязательные поля.")

    return redirect('record_detail', pk=pk)


@login_required
def edit_unplanned_expense(request, pk):
    """Редактирование существующего расхода"""
    expense = get_object_or_404(UnplannedExpense, id=pk)

    if request.method == 'POST':
        form = UnplannedExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Расход успешно обновлен!")
            return redirect('unplanned_expenses_list')
    else:
        form = UnplannedExpenseForm(instance=expense)

    return render(request, 'unplanned_expenses/edit.html', {
        'form': form,
        'expense': expense
    })


@login_required
def delete_unplanned_expense(request, pk):
    """Удаление непланируемого расхода - только для администраторов"""
    expense = get_object_or_404(UnplannedExpense, id=pk)
    record_id = expense.record.id
    
    # Проверка прав доступа - только администраторы могут удалять непланируемые расходы
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для удаления непланируемых расходов')
        return redirect('record_detail', pk=record_id)
    
    expense.delete()
    messages.success(request, "Расход успешно удален!")
    return redirect('record_detail', pk=record_id)

