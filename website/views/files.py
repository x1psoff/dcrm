"""Функции для работы с файлами"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
import pandas as pd
import os
from decimal import Decimal
from ..models import Record, UploadedFile


@login_required
def add_file(request, pk):
    """Добавление файлов к записи - доступно администраторам и рабочим"""
    from ..models import Profile
    record = get_object_or_404(Record, id=pk)
    
    # Проверка прав доступа
    if request.user.is_staff or request.user.is_superuser:
        pass
    else:
        try:
            profile = request.user.profile
            if profile and profile.designer:
                user_designer = profile.designer
                if not (record.designer == user_designer or 
                        record.designer_worker == user_designer or 
                        record.assembler_worker == user_designer):
                    messages.error(request, 'У вас нет прав для добавления файлов к этой записи')
                    return redirect('record_detail', pk=pk)
            else:
                messages.error(request, 'У вас нет прав для добавления файлов')
                return redirect('record_detail', pk=pk)
        except Profile.DoesNotExist:
            messages.error(request, 'У вас нет прав для добавления файлов')
            return redirect('record_detail', pk=pk)
    
    if request.method == 'POST' and 'file' in request.FILES:
        files = request.FILES.getlist('file')
        uploaded_count = 0
        for file in files:
            UploadedFile.objects.create(record=record, file=file)
            uploaded_count += 1
        if uploaded_count == 1:
            messages.success(request, "Файл успешно добавлен!")
        else:
            messages.success(request, f"Успешно добавлено файлов: {uploaded_count}")
    return redirect('record_detail', pk=pk)


def delete_file(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id)
    record_id = file.record.id
    file.delete()
    messages.success(request, "Файл успешно удален")
    return redirect('record_detail', pk=record_id)


def process_csv(request):
    record_id_raw = request.GET.get('record_id')
    if not record_id_raw:
        return render(request, 'error.html', {'error': 'Не указан ID записи'})

    record_id_clean = str(record_id_raw).strip().replace('{', '').replace('}', '').replace('%', '').replace('customer_record.id', '').strip()
    record_id_digits = ''.join(ch for ch in record_id_clean if ch.isdigit())
    try:
        record_id = int(record_id_digits)
    except (TypeError, ValueError):
        return render(request, 'error.html', {'error': f"Некорректный ID записи: {record_id_raw}"})

    record = get_object_or_404(Record, id=record_id)
    uploaded_files = record.files.all()
    files_data = []

    for uploaded_file in uploaded_files:
        file_info = {
            'file_name': os.path.basename(uploaded_file.file.name),
            'success': False
        }
        file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.file.name)

        try:
            df = pd.read_csv(file_path, sep=';', encoding='cp1251', header=None, engine='python', on_bad_lines='warn')
            if df.shape[1] < 5:
                raise ValueError("Файл должен содержать минимум 5 столбцов")

            for col in [2, 3, 4]:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df[2] = df[2].round() / 1000
            df[3] = df[3].round() / 1000
            filtered_df = df[df[4].isin([16, 18])].copy()
            filtered_df['area'] = (filtered_df[2] * filtered_df[3]).round(3)

            file_info.update({
                'data': filtered_df.to_dict('records'),
                'sum_16': filtered_df[filtered_df[4] == 16]['area'].sum().round(1),
                'sum_18': filtered_df[filtered_df[4] == 18]['area'].sum().round(1),
                'row_count': len(filtered_df),
                'success': True
            })
        except Exception as e:
            file_info['error'] = f"Ошибка обработки: {str(e)}"

        files_data.append(file_info)

    return render(request, 'process_csv.html', {
        'record': record,
        'files_data': files_data,
        'success_count': sum(1 for f in files_data if f['success'])
    })


def process_csv_by_pk(request, pk):
    """Альтернативный маршрут: принимает ID записи в URL без query-параметров."""
    from ..models import Designer
    record = get_object_or_404(Record, id=pk)
    uploaded_files = record.files.all()
    files_data = []
    total_area = 0

    for uploaded_file in uploaded_files:
        file_info = {
            'file_name': os.path.basename(uploaded_file.file.name),
            'success': False
        }
        file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.file.name)

        try:
            df = pd.read_csv(file_path, sep=';', encoding='cp1251', header=None, engine='python', on_bad_lines='warn')
            if df.shape[1] < 5:
                raise ValueError("Файл должен содержать минимум 5 столбцов")

            for col in [2, 3, 4]:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df[2] = df[2].round() / 1000
            df[3] = df[3].round() / 1000
            filtered_df = df[df[4].isin([16, 18])].copy()
            filtered_df['area'] = (filtered_df[2] * filtered_df[3]).round(3)

            file_area = filtered_df['area'].sum()
            total_area += file_area

            file_info.update({
                'data': filtered_df.to_dict('records'),
                'sum_16': filtered_df[filtered_df[4] == 16]['area'].sum().round(1),
                'sum_18': filtered_df[filtered_df[4] == 18]['area'].sum().round(1),
                'row_count': len(filtered_df),
                'success': True
            })
        except Exception as e:
            file_info['error'] = f"Ошибка обработки: {str(e)}"

        files_data.append(file_info)

    # Расчет зарплаты проектировщика
    designer_salary = 0
    designer_info = ''
    if record.designer and record.designer.rate_per_square_meter:
        d = record.designer
        try:
            total_area_dec = Decimal(str(total_area))
        except Exception:
            total_area_dec = Decimal('0')
        base_rate = d.rate_per_square_meter or Decimal('0')
        designer_salary = base_rate * total_area_dec
        designer_info = f"{d.name} {d.surname} — {d.rate_per_square_meter} ₽/м²"
    elif record.designer and record.designer.percentage and record.contract_amount:
        d = record.designer
        designer_salary = (record.contract_amount * d.percentage) / 100
        designer_info = f"{d.name} {d.surname} — {d.percentage}% от договора"

    return render(request, 'process_csv.html', {
        'record': record,
        'files_data': files_data,
        'success_count': sum(1 for f in files_data if f['success']),
        'total_area': round(total_area, 2),
        'designer_salary': designer_salary,
        'designer_info': designer_info,
    })

