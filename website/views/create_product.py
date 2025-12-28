"""View для создания продукта"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
from ..models import Product, Category, ProductCustomField, CategoryField


@login_required
def create_product(request):
    """Страница создания продукта с поддержкой характеристик"""
    
    if request.method == 'POST':
        # Получаем базовые данные
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        our_price = request.POST.get('our_price', '').strip()
        source_url = request.POST.get('source_url', '').strip()
        image = request.FILES.get('image')
        
        # Валидация
        if not name:
            messages.error(request, 'Название продукта обязательно')
            return redirect('create_product')
        
        if not our_price:
            messages.error(request, 'Цена продукта обязательна')
            return redirect('create_product')
        
        try:
            our_price = Decimal(our_price)
        except (InvalidOperation, ValueError):
            messages.error(request, 'Неверный формат цены')
            return redirect('create_product')
        
        # Нормализация ссылки (необязательно)
        if source_url and '://' not in source_url:
            source_url = 'https://' + source_url

        # Создаем продукт
        product = Product(name=name, our_price=our_price, source_url=source_url)
        
        # Изображение
        if image:
            product.image = image
        
        # Категория
        if category_id:
            try:
                product.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass
        
        product.save()
        
        # Добавляем характеристики
        if product.category:
            new_field_ids = request.POST.getlist('new_field[]')
            new_values = request.POST.getlist('new_value[]')
            new_template_names = request.POST.getlist('new_template_name[]')
            
            for i, (new_field_id, new_value) in enumerate(zip(new_field_ids, new_values)):
                new_value = new_value.strip()
                new_template_name = new_template_names[i].strip() if i < len(new_template_names) else ''
                
                if not new_value:
                    continue
                
                category_field = None
                
                # Если выбрано "Создать новый шаблон"
                if new_field_id == '__new__' and new_template_name:
                    try:
                        category_field, created = CategoryField.objects.get_or_create(
                            category=product.category,
                            name=new_template_name,
                            defaults={
                                'field_type': 'text',
                                'required': False
                            }
                        )
                        if created:
                            messages.success(request, f'Создан новый шаблон: {new_template_name}')
                    except Exception as e:
                        messages.error(request, f'Ошибка создания шаблона: {str(e)}')
                        continue
                
                # Если выбран существующий шаблон
                elif new_field_id and new_field_id != '__new__':
                    try:
                        new_field_id_int = int(new_field_id)
                        category_field = product.category.category_fields.get(id=new_field_id_int)
                    except (ValueError, CategoryField.DoesNotExist):
                        continue
                
                # Создаем ProductCustomField (проверяем, что не существует)
                if category_field:
                    ProductCustomField.objects.get_or_create(
                        product=product,
                        category_field=category_field,
                        defaults={'value': new_value, 'order': 0}
                    )
        
        messages.success(request, f'Продукт "{product.name}" успешно создан!')
        return redirect('product_detail', pk=product.id)
    
    # GET запрос
    category_id = request.GET.get('category')
    selected_category = None
    available_fields = []
    
    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id)
            available_fields = list(selected_category.get_fields())
        except Category.DoesNotExist:
            pass
    
    categories = Category.objects.all().order_by('name')
    
    return render(request, 'create_product.html', {
        'categories': categories,
        'selected_category': selected_category,
        'available_fields': available_fields,
    })


@login_required
@require_POST
def create_category(request):
    """Create a new product Category from UI (AJAX)."""
    name = (request.POST.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Название категории обязательно'}, status=400)

    # Deduplicate by case-insensitive match
    existing = Category.objects.filter(name__iexact=name).first()
    if existing:
        return JsonResponse({'ok': True, 'id': existing.id, 'name': existing.name, 'created': False})

    category = Category.objects.create(name=name)
    return JsonResponse({'ok': True, 'id': category.id, 'name': category.name, 'created': True})

