from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from urllib3 import request
from .models import Record, Product, Brand, Category, UnplannedExpense


class SignUpForm(UserCreationForm):
	email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
	first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
	last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


	def __init__(self, *args, **kwargs):
		super(SignUpForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['username'].widget.attrs['placeholder'] = 'User Name'
		self.fields['username'].label = ''
		self.fields['username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'

		self.fields['password1'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].widget.attrs['placeholder'] = 'Password'
		self.fields['password1'].label = ''
		self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

		self.fields['password2'].widget.attrs['class'] = 'form-control'
		self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
		self.fields['password2'].label = ''
		self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'


class RecordProductForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.select_related('category', 'brand').all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Комплектующие (выберите из списка)"
    )



    class Meta:
        model = Record
        fields = ['products']

class AddRecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['first_name', 'last_name', 'telegram', 'phone', 'address', 'city', 'kto', 'status', 'advance', 'contract_amount', 'designer']
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
        }
        labels = {
            'first_name': 'Индекс',
            'last_name': 'Наименование',
        }


class ProductFilterForm(forms.Form):
    name = forms.CharField(required=False, label="Название", widget=forms.TextInput(attrs={'class': 'form-control'}))

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label="Категория",
        empty_label="Все категории",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_category'})
    )

    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        label="Бренд",
        empty_label="Все бренды",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_brand'})
    )

    # Поля для петель
    hinge_angle = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in
                                 Product.objects.exclude(hinge_angle__isnull=True).exclude(hinge_angle='').values_list(
                                     'hinge_angle', flat=True).distinct()],
        required=False,
        label="Угол открывания",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    hinge_closing_type = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in Product.objects.exclude(hinge_closing_type__isnull=True).exclude(
            hinge_closing_type='').values_list('hinge_closing_type', flat=True).distinct()],
        required=False,
        label="Тип закрывания",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    response_type = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in Product.objects.exclude(response_type__isnull=True).exclude(
            response_type='').values_list('response_type', flat=True).distinct()],
        required=False,
        label="Тип ответки",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    mounting_type = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in Product.objects.exclude(mounting_type__isnull=True).exclude(
            mounting_type='').values_list('mounting_type', flat=True).distinct()],
        required=False,
        label="Тип монтажа",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Поля для направляющих
    runner_size = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in
                                 Product.objects.exclude(runner_size__isnull=True).exclude(runner_size='').values_list(
                                     'runner_size', flat=True).distinct()],
        required=False,
        label="Размер направляющих",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class HingeFilterForm(forms.Form):
    name = forms.CharField(required=False, label="Название", widget=forms.TextInput(attrs={'class': 'form-control'}))

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(name__icontains='петл'),
        required=False,
        label="Категория петель",
        empty_label="Все категории петель",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        label="Бренд",
        empty_label="Все бренды",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    hinge_angle = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in
                                 Product.objects.exclude(hinge_angle__isnull=True).exclude(hinge_angle='').values_list(
                                     'hinge_angle', flat=True).distinct()],
        required=False,
        label="Угол открывания",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    hinge_closing_type = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in Product.objects.exclude(hinge_closing_type__isnull=True).exclude(
            hinge_closing_type='').values_list('hinge_closing_type', flat=True).distinct()],
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

    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        label="Бренд",
        empty_label="Все бренды",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    runner_size = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in
                                 Product.objects.exclude(runner_size__isnull=True).exclude(runner_size='').values_list(
                                     'runner_size', flat=True).distinct()],
        required=False,
        label="Размер направляющих",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    response_type = forms.ChoiceField(
        choices=[('', 'Все')] + [(val, val) for val in Product.objects.exclude(response_type__isnull=True).exclude(
            response_type='').values_list('response_type', flat=True).distinct()],
        required=False,
        label="Тип ответки",
        widget=forms.Select(attrs={'class': 'form-control'})
    )