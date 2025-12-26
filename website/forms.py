from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.forms import inlineformset_factory
from django.db.models import Q
from urllib3 import request
from .models import Record, Product, Category, UnplannedExpense, ProductCustomField, CategoryField


class SignUpForm(UserCreationForm):
	first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Имя'}))
	last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Фамилия'}))

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'password1', 'password2')


	def __init__(self, *args, **kwargs):
		super(SignUpForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['username'].widget.attrs['placeholder'] = 'Логин'
		self.fields['username'].label = ''
		self.fields['username'].help_text = '<span class="form-text text-muted"><small>Обязательное поле. До 150 символов. Буквы, цифры и @/./+/-/_</small></span>'

		self.fields['password1'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
		self.fields['password1'].label = ''
		self.fields['password1'].help_text = '<span class="form-text text-muted"><small>Введите любой пароль</small></span>'

		self.fields['password2'].widget.attrs['class'] = 'form-control'
		self.fields['password2'].widget.attrs['placeholder'] = 'Подтвердите пароль'
		self.fields['password2'].label = ''
		self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Введите тот же пароль для подтверждения</small></span>'


class RecordProductForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(),  # Temporary fix - will be populated after migrations
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Комплектующие (выберите из списка)"
    )



    class Meta:
        model = Record
        fields = ['products']

class AddRecordForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='-- Не указан (можно оставить пустым) --',
        label='Заказчик',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Record
        fields = ['customer', 'first_name', 'last_name', 'telegram', 'phone', 'address', 'city', 'kto', 'status', 'advance', 'contract_amount', 'designer', 'designer_worker', 'assembler_worker', 'delivery_price', 'workshop_price', 'designer_manual_salary', 'designer_worker_manual_salary', 'assembler_worker_manual_salary']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Индекс'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Наименование'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telegram'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}),
            'status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Статус'}),
            'advance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'contract_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'designer': forms.Select(attrs={'class': 'form-control'}),
            'designer_worker': forms.Select(attrs={'class': 'form-control'}),
            'assembler_worker': forms.Select(attrs={'class': 'form-control'}),
            'delivery_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Цена доставки'}),
            'workshop_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Цена цеха'}),
            'designer_manual_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Погонные метры проектировщика'}),
            'designer_worker_manual_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Погонные метры дизайнера'}),
            'assembler_worker_manual_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Погонные метры сборщика'}),
        }
        labels = {
            'first_name': 'Индекс',
            'last_name': 'Наименование',
            'designer': 'Проектировщик',
            'designer_worker': 'Дизайнер',
            'assembler_worker': 'Сборщик',
            'delivery_price': 'Цена доставки',
            'workshop_price': 'Цена цеха',
            'designer_manual_salary': 'Погонные метры проектировщика',
            'designer_worker_manual_salary': 'Погонные метры дизайнера',
            'assembler_worker_manual_salary': 'Погонные метры сборщика',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        from .models import Profile
        
        # Показываем только заказчиков (без работников и администраторов)
        customers = User.objects.filter(
            is_staff=False,                      # Не администраторы
            profile__designer__isnull=True       # Нет назначенного работника
        ).order_by('username')
        
        self.fields['customer'].queryset = customers
        self.fields['customer'].label_from_instance = lambda obj: (
            f"{obj.get_full_name() or obj.username} (@{obj.username})"
        )


class ProductFilterForm(forms.Form):
    """Упрощенная форма фильтрации продуктов"""
    search = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Название...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label="Категория",
        empty_label="Все категории",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамически добавляем фильтры на основе полей категорий
        try:
            # Получаем все поля категорий
            from .models import CategoryField
            category_fields = CategoryField.objects.all().select_related('category').order_by('category__name', 'id')
            
            # Для каждого поля категории создаем фильтр
            for field in category_fields:
                field_key = field.field_key
                field_name = f'filter_{field_key}'
                
                # Получаем уникальные значения из custom_fields для этого поля
                values = set()
                
                # Получаем продукты этой категории
                # Не используем __has_key, так как он не поддерживается в SQLite
                products_with_category = Product.objects.filter(
                    category=field.category
                ).only('custom_fields', 'id')
                
                for product in products_with_category:
                    value = product.get_field_value(field_key)
                    if value and str(value).strip():
                        values.add(str(value).strip())
                
                # Создаем фильтр только если есть значения
                if values:
                    # Сортируем значения
                    sorted_values = sorted(values)
                    choices = [('', f'Все {field.name.lower()}')] + [(v, v) for v in sorted_values]
                    
                    self.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=False,
                        label=f"{field.category.name}: {field.name}",
                        widget=forms.Select(attrs={
                            'class': 'form-select form-select-sm',
                            'data-category': field.category.name,
                            'data-field-key': field_key
                        })
                    )
        except Exception as e:
            # Логируем ошибку для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ошибка создания динамических фильтров: {e}")


class HingeFilterForm(forms.Form):
    name = forms.CharField(required=False, label="Название", widget=forms.TextInput(attrs={'class': 'form-control'}))

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(name__icontains='петл'),
        required=False,
        label="Категория петель",
        empty_label="Все категории петель",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    hinge_angle = forms.ChoiceField(
        choices=[('', 'Все')],  # Temporary fix - will be populated after migrations
        required=False,
        label="Угол открывания",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    hinge_closing_type = forms.ChoiceField(
        choices=[('', 'Все')],  # Temporary fix - will be populated after migrations
        required=False,
        label="Тип закрывания",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    mounting_type = forms.ChoiceField(
        choices=[('', 'Все')] + [
            ('накладная', 'накладная'),
            ('полунакладная', 'полунакладная'),
            ('фальш-планка', 'фальш-планка'),
            ('вкладная', 'вкладная'),
            ('частичного выдвижения', 'частичного выдвижения'),
            ('полного выдвижения', 'полного выдвижения'),
            ('арик', 'арик'),
            ('телендо', 'телендо')
        ],
        required=False,
        label="Тип монтажа",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class UpdateRecordForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='-- Не указан (можно оставить пустым) --',
        label='Заказчик',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Record
        fields = ['customer', 'first_name', 'last_name', 'telegram', 'phone', 'address', 'city', 'kto', 'status', 'advance', 'contract_amount', 'designer', 'designer_worker', 'assembler_worker', 'delivery_price', 'workshop_price', 'designer_manual_salary', 'designer_worker_manual_salary', 'assembler_worker_manual_salary']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Индекс'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Наименование'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telegram'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}),
            'status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Статус'}),
            'advance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'contract_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'designer': forms.Select(attrs={'class': 'form-control'}),
            'designer_worker': forms.Select(attrs={'class': 'form-control'}),
            'assembler_worker': forms.Select(attrs={'class': 'form-control'}),
            'delivery_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Цена доставки'}),
            'workshop_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Цена цеха'}),
            'designer_manual_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Погонные метры проектировщика'}),
            'designer_worker_manual_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Погонные метры дизайнера'}),
            'assembler_worker_manual_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Погонные метры сборщика'}),
        }
        labels = {
            'first_name': 'Индекс',
            'last_name': 'Наименование',
            'designer': 'Проектировщик',
            'designer_worker': 'Дизайнер',
            'assembler_worker': 'Сборщик',
            'delivery_price': 'Цена доставки',
            'workshop_price': 'Цена цеха',
            'designer_manual_salary': 'Погонные метры проектировщика',
            'designer_worker_manual_salary': 'Погонные метры дизайнера',
            'assembler_worker_manual_salary': 'Погонные метры сборщика',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        from django.contrib.auth.models import User
        from .models import Profile
        
        # Показываем только заказчиков (без работников и администраторов)
        customers = User.objects.filter(
            is_staff=False,                      # Не администраторы
            profile__designer__isnull=True       # Нет назначенного работника
        ).order_by('username')
        
        self.fields['customer'].queryset = customers
        self.fields['customer'].label_from_instance = lambda obj: (
            f"{obj.get_full_name() or obj.username} (@{obj.username})"
        )
        
        # Получаем информацию о способах зарплаты для каждого рабочего
        self.designer_method = None
        self.designer_worker_method = None
        self.assembler_worker_method = None
        
        if self.instance:
            if self.instance.designer:
                self.designer_method = self.instance.designer.method
            if self.instance.designer_worker:
                self.designer_worker_method = self.instance.designer_worker.method
            if self.instance.assembler_worker:
                self.assembler_worker_method = self.instance.assembler_worker.method
        
        # Добавляем данные о способах зарплаты для JavaScript
        self.worker_methods_data = {}
        from .models import Designer
        for designer in Designer.objects.all():
            self.worker_methods_data[designer.id] = designer.method.name if designer.method else 'Не указан'

class UnplannedExpenseForm(forms.ModelForm):
    class Meta:
        model = UnplannedExpense
        fields = ['item', 'price']
        widgets = {
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название предмета'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Цена', 'step': '0.01'}),
        }
        labels = {
            'item': 'Предмет расхода',
            'price': 'Цена (руб.)',
        }

# Форма для фильтрации направляющих
class RunnerFilterForm(forms.Form):
    name = forms.CharField(required=False, label="Название", widget=forms.TextInput(attrs={'class': 'form-control'}))

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(name__icontains='направля'),
        required=False,
        label="Категория направляющих",
        empty_label="Все категории направляющих",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    runner_size = forms.ChoiceField(
        choices=[('', 'Все')],  # Temporary fix - will be populated after migrations
        required=False,
        label="Размер направляющих",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    response_type = forms.ChoiceField(
        choices=[('', 'Все')],  # Temporary fix - will be populated after migrations
        required=False,
        label="Тип ответки",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CreateProductForm(forms.ModelForm):
    """Форма для создания продукта на отдельной странице"""
    
    class Meta:
        model = Product
        fields = ['name', 'category', 'our_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название товара'}),
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'id_category'}),
            'our_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }
        labels = {
            'name': 'Название товара',
            'category': 'Категория',
            'our_price': 'Наша цена',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # Получаем категорию из POST данных или из instance
        category = None
        if instance:
            category = instance.category
        elif hasattr(self, 'data') and self.data and 'category' in self.data:
            try:
                category_id = self.data.get('category')
                if category_id:
                    category = Category.objects.get(id=category_id)
            except (ValueError, Category.DoesNotExist, TypeError):
                pass
        
        # Добавляем динамические поля для категории
        if category:
            try:
                category_fields = category.get_fields()
                for field in category_fields:
                    field_name = f'custom_field_{field.field_key}'
                    
                    initial_value = ''
                    if instance:
                        initial_value = instance.get_field_value(field.field_key) or ''
                    elif hasattr(self, 'data') and self.data and field_name in self.data:
                        initial_value = self.data.get(field_name, '')
                    
                    if field.field_type == 'text':
                        self.fields[field_name] = forms.CharField(
                            required=field.required,
                            label=field.name,
                            initial=initial_value,
                            widget=forms.TextInput(attrs={'class': 'form-control'})
                        )
                    elif field.field_type == 'number':
                        self.fields[field_name] = forms.DecimalField(
                            required=field.required,
                            label=field.name,
                            initial=initial_value if initial_value else None,
                            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
                        )
                    elif field.field_type == 'select':
                        choices = [('', '---------')] + [(c, c) for c in field.get_choices_list()]
                        self.fields[field_name] = forms.ChoiceField(
                            required=field.required,
                            label=field.name,
                            choices=choices,
                            initial=initial_value,
                            widget=forms.Select(attrs={'class': 'form-control'})
                        )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Ошибка загрузки полей категории: {e}")
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Сохраняем значения динамических полей в custom_fields
        if instance.category:
            category_fields = instance.category.get_fields()
            if not instance.custom_fields:
                instance.custom_fields = {}
            
            for field in category_fields:
                field_name = f'custom_field_{field.field_key}'
                if field_name in self.cleaned_data:
                    instance.set_field_value(field.field_key, self.cleaned_data[field_name])
        
        if commit:
            instance.save()
        return instance


# Formset для индивидуальных характеристик продукта
class BaseProductCustomFieldFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем шаблоны по категории продукта
        if self.instance and self.instance.category:
            for form in self.forms:
                if 'category_field' in form.fields:
                    form.fields['category_field'].queryset = CategoryField.objects.filter(
                        category=self.instance.category
                    )


ProductCustomFieldFormSet = inlineformset_factory(
    Product,
    ProductCustomField,
    formset=BaseProductCustomFieldFormSet,
    fields=('category_field', 'value', 'order'),
    extra=1,
    can_delete=True,
    widgets={
        'category_field': forms.Select(attrs={'class': 'form-control category-field-select'}),
        'value': forms.TextInput(attrs={'class': 'form-control'}),
        'order': forms.NumberInput(attrs={'class': 'form-control', 'type': 'number', 'min': '0'}),
    }
)