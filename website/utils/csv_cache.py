"""Утилита для кэширования чтения CSV файлов"""
import pandas as pd
import os
import hashlib
from django.core.cache import cache
from django.conf import settings


def calculate_file_area(file_path):
    """
    Вычисляет площадь из CSV файла.
    Обрабатывает файл с разделителем ';', кодировкой cp1251.
    """
    try:
        df = pd.read_csv(file_path, sep=';', encoding='cp1251', header=None, engine='python', on_bad_lines='warn')
        if df.shape[1] < 5:
            return 0
        
        # Преобразуем столбцы в числовые
        for col in [2, 3, 4]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Конвертируем из мм в метры
        df[2] = df[2].round() / 1000
        df[3] = df[3].round() / 1000
        
        # Фильтруем по типу (16 или 18)
        filtered_df = df[df[4].isin([16, 18])].copy()
        filtered_df['area'] = (filtered_df[2] * filtered_df[3]).round(3)
        
        return float(filtered_df['area'].sum())
    except Exception:
        return 0


def get_file_cache_key(file_path, file_modified_time):
    """Генерирует ключ кэша на основе пути файла и времени модификации"""
    # Используем путь и время модификации для уникальности
    cache_data = f"{file_path}:{file_modified_time}"
    return f"csv_area:{hashlib.md5(cache_data.encode()).hexdigest()}"


def get_record_files_area(record):
    """
    Вычисляет общую площадь из всех CSV файлов записи с кэшированием.
    Возвращает сумму площадей всех файлов.
    """
    uploaded_files = record.files.all()
    total_area = 0
    
    for uploaded_file in uploaded_files:
        file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.file.name)
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            continue
        
        # Получаем время модификации файла для инвалидации кэша
        try:
            file_mtime = os.path.getmtime(file_path)
        except Exception:
            file_mtime = 0
        
        # Генерируем ключ кэша
        cache_key = get_file_cache_key(file_path, file_mtime)
        
        # Пытаемся получить из кэша
        cached_area = cache.get(cache_key)
        if cached_area is not None:
            total_area += cached_area
            continue
        
        # Если нет в кэше, вычисляем
        area = calculate_file_area(file_path)
        
        # Сохраняем в кэш на 1 час (3600 секунд)
        cache.set(cache_key, area, 3600)
        
        total_area += area
    
    return total_area

