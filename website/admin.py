# admin.py
from django.contrib import admin
from django import forms
from django.utils import timezone
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
import re
from .models import Category, Product, Store, Brand, CalculationMethod, Designer,Plita,RecordPlita
from django.urls import path
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
import logging
from django.utils.safestring import mark_safe

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    list_filter = ['parent']
    search_fields = ['name']


class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'url_pattern', 'price_selector', 'discount_percent']
    search_fields = ['name']


class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class CalculationMethodAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class DesignerAdmin(admin.ModelAdmin):
    list_display = ['name', 'surname', 'method']
    list_filter = ['method']
    search_fields = ['name', 'surname']


class ProductAdminForm(forms.ModelForm):
    parse_now = forms.BooleanField(
        required=False,
        label="Запарсить сейчас"
    )

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'mounting_type': forms.Select(choices=[]),
            'response_type': forms.Select(choices=[]),
            'hinge_angle': forms.Select(choices=[]),
            'hinge_closing_type': forms.Select(choices=[]),
            'runner_size': forms.Select(choices=[]),
        }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['id', 'name', 'category', 'brand', 'mounting_type', 'response_type', 'hinge_angle',
                    'hinge_closing_type', 'runner_size', 'our_price',
                    'parsed_price', 'get_our_price_with_discount', 'last_parsed']
    list_display_links = ['id', 'name']
    list_filter = ['category', 'brand', 'store', 'mounting_type', 'response_type', 'hinge_angle', 'hinge_closing_type',
                   'runner_size']
    search_fields = ['name', 'category__name', 'brand__name', 'id']
    readonly_fields = ['id', 'last_parsed', 'parsed_price', 'get_price_comparison', 'product_characteristics']

    fieldsets = (
        ('Характеристики товара', {
            'fields': ('product_characteristics',),
            'classes': ('characteristics-panel',),
        }),
        ('Основная информация', {
            'fields': (
                'id', 'name', 'category', ('brand', 'store'), 'source_url',
                'mounting_type', 'response_type', 'hinge_angle', 'hinge_closing_type', 'runner_size'
            ),
            'classes': ('wide',),
        }),
        ('Цены', {
            'fields': (
                'our_price',
                'get_price_comparison',
                'parse_now'
            )
        }),
    )

    def product_characteristics(self, obj):
        """Отображение характеристик товара в зависимости от категории"""
        if not obj.id:
            return "Сохраните товар, чтобы увидеть характеристики"

        if not obj.category:
            return "Выберите категорию товара"

        category_name = obj.category.name.lower()

        # Для петель
        if 'петл' in category_name:
            characteristics = []
            if obj.mounting_type:
                characteristics.append(f"<b>Тип:</b> {obj.mounting_type}")
            if obj.response_type:
                characteristics.append(f"<b>Тип ответки:</b> {obj.response_type}")
            if obj.hinge_angle:
                characteristics.append(f"<b>Угол открывания:</b> {obj.hinge_angle}°")
            if obj.hinge_closing_type:
                characteristics.append(f"<b>Тип закрывания:</b> {obj.hinge_closing_type}")

            if characteristics:
                return mark_safe("<br>".join(characteristics))
            else:
                return "Заполните характеристики для петель"

        # Для направляющих
        elif 'направля' in category_name:
            characteristics = []
            if obj.mounting_type:
                characteristics.append(f"<b>Тип:</b> {obj.mounting_type}")
            if obj.runner_size:
                characteristics.append(f"<b>Размер направляющих:</b> {obj.runner_size} мм")

            if characteristics:
                return mark_safe("<br>".join(characteristics))
            else:
                return "Заполните характеристики для направляющих"

        # Для других категорий
        else:
            return "Характеристики не определены для этой категории"

    product_characteristics.short_description = 'Характеристики товара'

    def get_price_comparison(self, obj):
        """Объединенное отображение цен со скидкой и без"""
        if not obj.parsed_price:
            return "Цена не получена"

        result = []
        result.append(f"В интернете: {obj.parsed_price} ₽")

        if obj.store and obj.store.discount_percent:
            discount = obj.parsed_price * (obj.store.discount_percent / 100)
            final_price = obj.parsed_price - discount
            result.append(f"Цена со скидкой %{obj.store.discount_percent:.0f}: {final_price:.1f} ₽")
        else:
            result.append(f"Наша цена: {obj.parsed_price} ₽ (скидка не применена)")

        return "ㅤㅤㅤㅤㅤㅤ".join(result)

    get_price_comparison.short_description = 'В магазине '
    get_price_comparison.allow_tags = True

    def get_our_price_with_discount(self, obj):
        """Цена со скидкой магазина для списка"""
        if obj.final_parsed_price:
            return f"{obj.final_parsed_price} ₽"
        return "Не рассчитано"

    get_our_price_with_discount.short_description = 'Наша цена'

    def save_model(self, request, obj, form, change):
        # Обрабатываем парсинг цены
        if form.cleaned_data.get('parse_now') and obj.source_url:
            try:
                parsed_price = self.parse_price(obj.source_url, obj.store)
                obj.parsed_price = parsed_price
                obj.last_parsed = timezone.now()
            except Exception as e:
                self.message_user(request, f"Ошибка парсинга: {str(e)}", level='ERROR')

        super().save_model(request, obj, form, change)

    def parse_price(self, url, store):
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

            # Если указан магазин, используем его селектор
            if store and store.price_selector:
                price_element = soup.select_one(store.price_selector)
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
            price = self.parse_price(product.source_url, product.store)
            product.parsed_price = price
            product.last_parsed = timezone.now()
            product.save()
            return JsonResponse({'success': True, 'price': str(price)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    class Media:
        js = ('js/product_discount.js', 'js/mounting_type.js')
        css = {
            'all': ('css/admin_custom.css',)
        }

@admin.register(Plita)
class PlitaAdmin(admin.ModelAdmin):
    list_display = ['name', 'material', 'thickness', 'color', 'price_per_square_meter']
    list_filter = ['material', 'thickness']
    search_fields = ['name', 'material', 'color']
    ordering = ['material', 'thickness', 'name']

@admin.action(description="Запарсить цены для выбранных товаров")
def parse_selected_prices(modeladmin, request, queryset):
    success = 0
    errors = 0

    for product in queryset:
        if product.source_url:
            try:
                parsed_price = modeladmin.parse_price(product.source_url, product.store)
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
admin.site.register(Store, StoreAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(CalculationMethod, CalculationMethodAdmin)
admin.site.register(Designer, DesignerAdmin)
admin.site.register(RecordPlita)