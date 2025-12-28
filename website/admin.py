# admin.py
from django.contrib import admin
from django import forms
from django.utils import timezone
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
import re
from .models import Category, CategoryField, Product, ProductCustomField, CalculationMethod, Profession, Designer, Profile, WorkerPayment, WorkerPaymentDeduction
from django.urls import path
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
import logging
from django.utils.safestring import mark_safe

# Логирование (уровень задаётся настройками Django/окружением; не выставляем basicConfig глобально)
logger = logging.getLogger(__name__)


class CategoryFieldInline(admin.TabularInline):
    model = CategoryField
    extra = 1
    fields = ('name', 'field_type', 'required')
    ordering = ('id',)
    verbose_name = "Характеристика"
    verbose_name_plural = "Характеристики категории"
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Улучшаем подсказки для полей
        class CategoryFieldForm(formset.form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Добавляем подсказки
                if 'name' in self.fields:
                    self.fields['name'].help_text = 'Например: Угол открывания, Тип ответки, Длина'
                if 'field_type' in self.fields:
                    self.fields['field_type'].help_text = 'Текст - для обычных значений, Число - для размеров, Выбор - для списка вариантов'
        
        formset.form = CategoryFieldForm
        
        # Автоматически генерируем field_key из названия
        class CategoryFieldFormSet(formset):
            def save_new(self, form, commit=True):
                instance = form.save(commit=False)
                if not instance.field_key:
                    # Генерируем ключ из названия
                    import re
                    key = instance.name.lower()
                    # Транслитерация
                    translit_map = {
                        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
                        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
                        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
                        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
                        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
                    }
                    for ru, en in translit_map.items():
                        key = key.replace(ru, en)
                    key = re.sub(r'[^\w\s-]', '', key)
                    key = re.sub(r'[-\s]+', '_', key)
                    key = key.strip('_')
                    instance.field_key = key
                if commit:
                    instance.save()
                return instance
            
            def save_existing(self, form, instance, commit=True):
                obj = form.save(commit=False)
                # Обновляем ключ автоматически
                import re
                key = obj.name.lower()
                translit_map = {
                    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
                    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
                    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
                    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
                    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
                }
                for ru, en in translit_map.items():
                    key = key.replace(ru, en)
                key = re.sub(r'[^\w\s-]', '', key)
                key = re.sub(r'[-\s]+', '_', key)
                key = key.strip('_')
                obj.field_key = key
                if commit:
                    obj.save()
                return obj
        
        return CategoryFieldFormSet


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'fields_count']
    search_fields = ['name']
    # В админке не показываем "поля категорий" (шаблоны характеристик) — управляется из UI
    inlines = []
    
    fieldsets = (
        ('Название категории', {
            'fields': ('name',),
        }),
    )
    
    def fields_count(self, obj):
        count = obj.category_fields.count()
        if count > 0:
            return f"{count} шаблонов"
        return "Нет шаблонов"
    fields_count.short_description = 'Шаблоны'


class CalculationMethodAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class ProfessionAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class DesignerAdmin(admin.ModelAdmin):
    list_display = ['name', 'surname', 'profession', 'method']
    list_filter = ['profession', 'method']
    search_fields = ['name', 'surname']


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'our_price',
            'custom_fields',
            'mounting_type',
            'response_type',
            'hinge_angle',
            'hinge_closing_type',
            'runner_size',
        ]
        widgets = {
            'mounting_type': forms.Select(choices=[]),
            'response_type': forms.Select(choices=[]),
            'hinge_angle': forms.Select(choices=[]),
            'hinge_closing_type': forms.Select(choices=[]),
            'runner_size': forms.Select(choices=[]),
            'custom_fields': forms.HiddenInput(),  # Скрываем JSONField, будем работать через динамические поля
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамические поля категории в админке отключены, чтобы избежать рекурсий и предупреждений.
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class ProductCustomFieldInline(admin.TabularInline):
    model = ProductCustomField
    extra = 1
    fields = ('category_field', 'value', 'order')
    ordering = ('order', 'id')
    verbose_name = "Индивидуальная характеристика"
    verbose_name_plural = "Индивидуальные характеристики"
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        class ProductCustomFieldForm(formset.form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Фильтруем шаблоны по категории продукта
                if obj and obj.category:
                    if 'category_field' in self.fields:
                        self.fields['category_field'].queryset = CategoryField.objects.filter(
                            category=obj.category
                        )
                        self.fields['category_field'].help_text = 'Выберите шаблон из характеристик категории'
                        self.fields['category_field'].required = True
                else:
                    if 'category_field' in self.fields:
                        self.fields['category_field'].queryset = CategoryField.objects.none()
                        self.fields['category_field'].help_text = 'Сначала выберите категорию для продукта'
        
        formset.form = ProductCustomFieldForm
        return formset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['id', 'name', 'category', 'our_price', 'last_parsed']
    list_display_links = ['id', 'name']
    list_filter = ['category']
    search_fields = ['name', 'category__name', 'id']
    readonly_fields = ['id', 'last_parsed', 'product_characteristics']
    inlines = [ProductCustomFieldInline]

    def get_fieldsets(self, request, obj=None):
        """Полеsets без динамических полей категории"""
        fieldsets = [
            ('Характеристики товара', {
                'fields': ('product_characteristics',),
                'classes': ('characteristics-panel',),
            }),
            ('Основная информация', {
                'fields': (
                    'id', 'name', 'category',
                ),
                'classes': ('wide',),
            }),
        ]
        fieldsets.append(('Цены', {
            'fields': (
                'our_price',
            )
        }))
        
        return fieldsets

    def product_characteristics(self, obj):
        """Отображение характеристик товара из полей категории и индивидуальных"""
        if not obj.id:
            return "Сохраните товар, чтобы увидеть характеристики"

        characteristics = []
        
        # Показываем характеристики из полей категории
        if obj.category:
            category_fields = obj.get_category_fields()
            for item in category_fields:
                field = item['field']
                value = item['value']
                if value:
                    characteristics.append(f"<b>{field.name}:</b> {value}")
        
        # Показываем индивидуальные характеристики (из шаблонов)
        custom_fields = obj.get_custom_characteristics()
        for custom_field in custom_fields:
            if custom_field.value:
                characteristics.append(f"<b>{custom_field.name}:</b> {custom_field.value}")
        
        if characteristics:
            return mark_safe("<br>".join(characteristics))
        else:
            msg = []
            if obj.category:
                if obj.category.category_fields.exists():
                    msg.append("Добавьте индивидуальные характеристики через вкладку 'Индивидуальные характеристики', выбрав шаблоны из категории.")
                else:
                    msg.append("Сначала создайте шаблоны характеристик в категории, затем добавьте их к продукту.")
            else:
                msg.append("Выберите категорию для продукта, чтобы добавить индивидуальные характеристики.")
            return " ".join(msg)

    product_characteristics.short_description = 'Характеристики товара'

    def get_price_comparison(self, obj):
        """Отображение цены после парсинга"""
        if not obj.parsed_price:
            return "Цена не получена"

        return f"В интернете: {obj.parsed_price} ₽"

    get_price_comparison.short_description = 'В магазине '
    get_price_comparison.allow_tags = True

    def get_our_price_with_discount(self, obj):
        """Цена со скидкой магазина для списка"""
        if obj.final_parsed_price:
            return f"{obj.final_parsed_price} ₽"
        return "Не рассчитано"

    get_our_price_with_discount.short_description = 'Наша цена'

    def parse_price(self, url):
        """Универсальная функция парсинга цены"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
            }
            logger.debug(f"Попытка запроса к {url}")
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            logger.debug(f"Статус: {response.status_code}")
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Пробуем стандартные селекторы для популярных селекторов цен
            price_element = None
            # Здесь можно добавить стандартные селекторы для различных сайтов
            if price_element:
                return self.extract_price_from_text(price_element.get_text())

            # Автоопределение для MDM
            if 'mdm-' in url or 'mdm.com' in url:
                price_element = soup.select_one('.price-main')
                if price_element:
                    return self.extract_price_from_text(price_element.get_text())

            # Универсальные селекторы
            universal_selectors = [
                '.price', '.product-price', '[itemprop="price"]',
                '.current-price', '.js-product-price', '.price-value'
            ]
            for selector in universal_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price = self.extract_price_from_text(price_element.get_text())
                    if price:
                        return price

            raise ValueError("Цена не найдена на странице")

        except Exception as e:
            logger.error(f"Ошибка парсинга: {str(e)}")
            raise Exception(f"Ошибка парсинга: {str(e)}")

    def extract_price_from_text(self, text):
        """Извлекает цену из текста"""
        text = text.strip().replace(' ', '').replace(',', '.').replace('₽', '')
        patterns = [
            r'(\d+[\.,]\d{2})',  # 123.45 или 123,45
            r'(\d+)',  # 12345
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '.')
                try:
                    return Decimal(price_str)
                except:
                    continue
        return None

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/parse-price/',
                self.admin_site.admin_view(self.parse_price_view),
                name='product_parse_price',
            ),
        ]
        return custom_urls + urls

    def parse_price_view(self, request, object_id):
        product = get_object_or_404(Product, id=object_id)
        try:
            price = self.parse_price(product.source_url)
            product.parsed_price = price
            product.last_parsed = timezone.now()
            product.save()
            return JsonResponse({'success': True, 'price': str(price)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    class Media:
        js = ('js/product_discount.js', 'js/mounting_type.js', 'js/category_fields.js')
        css = {
            'all': ('css/admin_custom.css',)
        }
    
    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем get_form для правильной работы с динамическими полями"""
        form = super().get_form(request, obj, **kwargs)
        return form

# Плиты больше не используются

@admin.action(description="Запарсить цены для выбранных товаров")
def parse_selected_prices(modeladmin, request, queryset):
    success = 0
    errors = 0

    for product in queryset:
        if product.source_url:
            try:
                parsed_price = modeladmin.parse_price(product.source_url)
                product.parsed_price = parsed_price
                product.last_parsed = timezone.now()
                product.save()
                success += 1
            except:
                errors += 1

    modeladmin.message_user(
        request,
        f"Успешно: {success}, Ошибок: {errors}"
    )


ProductAdmin.actions = [parse_selected_prices]

# Регистрируем модели
admin.site.register(Category, CategoryAdmin)
# CategoryField (поля категорий) скрываем из админки
admin.site.register(CalculationMethod, CalculationMethodAdmin)
admin.site.register(Profession, ProfessionAdmin)
admin.site.register(Designer, DesignerAdmin)
# RecordPlita удалена - плиты теперь используют RecordProduct
admin.site.register(Profile)


@admin.register(WorkerPayment)
class WorkerPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'worker', 'record', 'role', 'amount', 'is_paid', 'paid_at', 'created_at']
    list_filter = ['is_paid', 'role', 'created_at', 'paid_at']
    search_fields = ['worker__name', 'worker__surname', 'record__first_name', 'record__last_name', 'record__id']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_paid']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('record', 'worker', 'role', 'amount')
        }),
        ('Статус оплаты', {
            'fields': ('is_paid', 'paid_at')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Автоматически устанавливаем paid_at при отметке как оплачено
        if obj.is_paid and not obj.paid_at:
            from django.utils import timezone
            obj.paid_at = timezone.now()
        elif not obj.is_paid:
            obj.paid_at = None
        super().save_model(request, obj, form, change)


@admin.register(WorkerPaymentDeduction)
class WorkerPaymentDeductionAdmin(admin.ModelAdmin):
    list_display = ["id", "payment", "amount", "reason", "created_at"]
    list_filter = ["created_at"]
    search_fields = [
        "reason",
        "payment__worker__name",
        "payment__worker__surname",
        "payment__record__first_name",
        "payment__record__last_name",
        "payment__record__id",
    ]
    ordering = ["-created_at", "-id"]