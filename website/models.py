from django.db import models
from django.contrib.auth.models import User






class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")

    def get_fields(self):
        """Получить все поля категории"""
        return self.category_fields.all().order_by('id')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class CategoryField(models.Model):
    """Поля для категории - определяют какие характеристики можно задавать для продуктов этой категории"""
    FIELD_TYPE_CHOICES = [
        ('text', 'Текст'),
        ('number', 'Число'),
        ('select', 'Выбор из списка'),
    ]
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_fields',
        verbose_name="Категория"
    )
    name = models.CharField(max_length=100, verbose_name="Название поля", help_text="Например: Угол открывания, Тип ответки, Длина")
    field_key = models.SlugField(
        max_length=100, 
        verbose_name="Ключ поля", 
        help_text="Автоматически генерируется из названия",
        blank=True
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default='text',
        verbose_name="Тип поля",
        help_text="Текст - для обычных значений, Число - для размеров/количеств, Выбор - для списка вариантов"
    )
    required = models.BooleanField(default=False, verbose_name="Обязательное", help_text="Обязательно ли заполнять это поле")
    
    def save(self, *args, **kwargs):
        # Автоматически генерируем field_key из названия, если не указан
        if not self.field_key:
            import re
            key = self.name.lower()
            # Транслитерация основных русских букв
            translit_map = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
                'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
                'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
                'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
                'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
            }
            for ru, en in translit_map.items():
                key = key.replace(ru, en)
            # Убираем спецсимволы, оставляем только буквы, цифры, пробелы и дефисы
            key = re.sub(r'[^\w\s-]', '', key)
            # Заменяем пробелы и дефисы на подчеркивания
            key = re.sub(r'[-\s]+', '_', key)
            key = key.strip('_')
            self.field_key = key
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        verbose_name = "Поле категории"
        verbose_name_plural = "Поля категорий"
        unique_together = ['category', 'field_key']
        ordering = ['id']


class CalculationMethod(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название метода")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Способ оплаты раб"
        verbose_name_plural = "Способы оплаты раб"


class Profession(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название профессии")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Профессия"
        verbose_name_plural = "Профессии"


class Designer(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    surname = models.CharField(max_length=100, verbose_name="Фамилия")
    profession = models.ForeignKey(
        Profession,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        verbose_name="Профессия"
    )
    method = models.ForeignKey(
        CalculationMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        verbose_name="Метод расчета"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Процент от договора"
    )
    rate_per_square_meter = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ставка за м²"
    )

    def __str__(self):
        return f"{self.name} {self.surname}"

    class Meta:
        verbose_name = "Рабочий"
        verbose_name_plural = "Рабочие"


# Модель Plita удалена - плиты больше не используются
# Модели Brand и Store удалены - бренды и магазины больше не используются

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название товара")

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Категория"
    )

    # Старые поля оставляем для обратной совместимости, но они будут deprecated
    hinge_angle = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Угол открывания (устарело)"
    )

    hinge_closing_type = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Тип закрывания (устарело)"
    )

    runner_size = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Размер направляющих (устарело)"
    )

    response_type=models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Тип ответки (устарело)"
    )

    mounting_type = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Тип (устарело)"
    )

    # Новое поле для хранения динамических характеристик
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Дополнительные характеристики",
        help_text="Хранит значения полей, определенных для категории"
    )

    our_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Наша цена"
    )
    parsed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена со скидкой"
    )
    source_url = models.URLField(
        verbose_name="URL для парсинга",
        blank=True
    )
    last_parsed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последний парсинг"
    )
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True,
        verbose_name="Изображение продукта"
    )

    def get_field_value(self, field_key):
        """Получить значение поля по ключу"""
        return self.custom_fields.get(field_key, '')
    
    def set_field_value(self, field_key, value):
        """Установить значение поля"""
        if not self.custom_fields:
            self.custom_fields = {}
        self.custom_fields[field_key] = value
    
    def get_category_fields(self):
        """Получить все поля категории с их значениями"""
        if not self.category:
            return []
        
        fields = self.category.get_fields()
        result = []
        for field in fields:
            result.append({
                'field': field,
                'value': self.get_field_value(field.field_key)
            })
        return result
    
    def get_custom_characteristics(self):
        """Получить все индивидуальные характеристики продукта"""
        return self.product_custom_fields.all().order_by('order', 'id')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Элемент"
        verbose_name_plural = "Элементы"


    @property
    def final_parsed_price(self):
        """Итоговая цена после парсинга"""
        return round(self.parsed_price, 1) if self.parsed_price else 0

class ProductCustomField(models.Model):
    """Индивидуальные характеристики для конкретного продукта - выбираются из шаблонов категории"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_custom_fields',
        verbose_name="Продукт"
    )
    category_field = models.ForeignKey(
        CategoryField,
        on_delete=models.CASCADE,
        related_name='product_custom_fields',
        verbose_name="Шаблон характеристики",
        help_text="Выберите шаблон из характеристик категории этого продукта",
        null=True,
        blank=True
    )
    value = models.CharField(max_length=500, verbose_name="Значение", blank=True)
    order = models.IntegerField(default=0, verbose_name="Порядок")
    
    @property
    def name(self):
        """Название из шаблона"""
        return self.category_field.name if self.category_field else ""
    
    @property
    def field_type(self):
        """Тип поля из шаблона"""
        return self.category_field.field_type if self.category_field else 'text'
    
    def get_choices_list(self):
        """Получить список вариантов для выбора из шаблона"""
        # Варианты выбора больше не поддерживаются в шаблонах
        return []
    
    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"
    
    class Meta:
        verbose_name = "Индивидуальная характеристика"
        verbose_name_plural = "Индивидуальные характеристики"
        ordering = ['order', 'id']
        unique_together = ['product', 'category_field']


class Record(models.Model):
    STATUS_CHOICES = [
        ('otrisovka', 'Отрисовка'),
        ('zhdem_material', 'Ждем прибытия материала'),
        ('priekhal_v_ceh', 'Приехал в цех'),
        ('na_raspile', 'На распиле'),
        ('zakaz_gotov', 'Заказ готов'),
    ]
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_records',
        verbose_name='Заказчик (необязательно)'
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    telegram = models.CharField(max_length=100, blank=True, default='', verbose_name="Telegram")
    phone = models.CharField(max_length=15, blank=True, default='')
    address = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=50, blank=True, default='')
    state = models.CharField(max_length=50, blank=True, default='')
    zipcode = models.CharField(max_length=20, blank=True, default='')
    kto = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='otrisovka',
        verbose_name="Статус заказа",
        db_index=True
    )
    advance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Аванс")
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Сумма по договору")
    designer = models.ForeignKey(
        Designer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Проектировщик"
    )
    # Ручной ввод погонных метров для каждого рабочего
    designer_manual_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Погонные метры проектировщика"
    )
    designer_worker_manual_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Погонные метры дизайнера"
    )
    assembler_worker_manual_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Погонные метры сборщика"
    )
    
    # Поля для других профессий
    designer_worker = models.ForeignKey(
        Designer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='designer_records',
        verbose_name="Дизайнер",
        limit_choices_to={'profession__name': 'дизайнер'}
    )
    assembler_worker = models.ForeignKey(
        Designer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assembler_records',
        verbose_name="Сборщик",
        limit_choices_to={'profession__name': 'сборщики'}
    )
    delivery_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена доставки"
    )
    workshop_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена цеха"
    )
    # Отметки для распределения моржи
    margin_yura = models.BooleanField(default=True, verbose_name="Моржа Юра")
    margin_oleg = models.BooleanField(default=True, verbose_name="Моржа Олег")

    products = models.ManyToManyField(Product, related_name='records', blank=True, verbose_name="Комплектующие")
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class RecordProduct(models.Model):
    BUYER_CHOICES = [
        ('Юра', 'Юра'),
        ('Олег', 'Олег'),
    ]

    record = models.ForeignKey(Record, on_delete=models.CASCADE, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_index=True)
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    added_at = models.DateTimeField(auto_now_add=True)
    buyer = models.CharField(
        max_length=10,
        choices=BUYER_CHOICES,
        default='Юра',
        verbose_name="Кто купил"
    )
    custom_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Своя цена за единицу"
    )

    class Meta:
        unique_together = ['record', 'product']

    def __str__(self):
        return f"{self.record} - {self.product} x{self.quantity} ({self.buyer})"
class UploadedFile(models.Model):
    def upload_to_path(instance, filename):
        return f'uploads/record_{instance.record.id}/{filename}'

    record = models.ForeignKey(Record, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to=upload_to_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class UnplannedExpense(models.Model):
    SPENT_BY_CHOICES = [
        ('Юра', 'Юра'),
        ('Олег', 'Олег'),
        # Можно добавить других людей в будущем
    ]

    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='unplanned_expenses',
        verbose_name="Запись",
        db_index=True
    )
    item = models.CharField(max_length=200, verbose_name="Предмет расхода")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена"
    )
    spent_by = models.CharField(
        max_length=50,
        choices=SPENT_BY_CHOICES,
        default='Юра',
        verbose_name="Кто потратил",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.item} - {self.price} руб. ({self.spent_by})"

    class Meta:
        verbose_name = "Непланируемый расход"
        verbose_name_plural = "Непланируемые расходы"
        ordering = ['-created_at']


class Profile(models.Model):
    """Профиль пользователя с привязкой к работнику (Designer)"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    designer = models.ForeignKey(
        Designer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
        verbose_name='Проектировщик/Дизайнер/Сборщик'
    )
    telegram_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        verbose_name='Telegram ID'
    )
    telegram_verified = models.BooleanField(
        default=False,
        verbose_name='Telegram подтвержден'
    )
    verification_code = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        verbose_name='Код верификации'
    )

    def __str__(self):
        return f"Профиль {self.user.username}"
    
    @property
    def is_worker(self):
        """Проверяет, является ли пользователь работником"""
        return bool(self.designer)
    
    @property
    def is_customer(self):
        """Проверяет, является ли пользователь заказчиком"""
        return not self.is_worker and not self.user.is_staff
    
    @property
    def user_type_display(self):
        """Возвращает текстовое представление типа пользователя"""
        if self.user.is_superuser:
            return "Администратор"
        elif self.user.is_staff:
            return "Менеджер"
        elif self.is_worker:
            return "Работник"
        else:
            return "Заказчик"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class WorkerPayment(models.Model):
    """Модель для отслеживания выплат работникам"""
    ROLE_CHOICES = [
        ('designer', 'Проектировщик'),
        ('designer_worker', 'Дизайнер'),
        ('assembler_worker', 'Сборщик'),
    ]
    
    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='worker_payments',
        verbose_name="Запись"
    )
    worker = models.ForeignKey(
        Designer,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Работник"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="Роль"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Сумма выплаты"
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name="Оплачено",
        db_index=True
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата оплаты"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "Выплата работнику"
        verbose_name_plural = "Выплаты работникам"
        unique_together = ['record', 'worker', 'role']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_paid', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.worker.name} {self.worker.surname} - {self.get_role_display()} - {self.amount} ₽ ({'Оплачено' if self.is_paid else 'Не оплачено'})"