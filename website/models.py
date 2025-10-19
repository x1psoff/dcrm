from django.db import models






class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Фурнитура"
    )

    def get_brands(self):
        return Brand.objects.filter(product__category=self).distinct()

    def get_root_categories(self):
        """Получить все корневые категории (без родителя)"""
        return Category.objects.filter(parent__isnull=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class CalculationMethod(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название метода")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Способ оплаты раб"
        verbose_name_plural = "Способы оплаты раб"


class Designer(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    surname = models.CharField(max_length=100, verbose_name="Фамилия")
    method = models.ForeignKey(
        CalculationMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        verbose_name = "Проектировщик"
        verbose_name_plural = "Проектировщики"


class Plita(models.Model):
    MATERIAL_CHOICES = [
        ('ЛДСП', 'ЛДСП'),
        ('МДФ', 'МДФ'),
        ('Пленка', 'Пленка'),
        ('Другой', 'Другой материал'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название плиты")
    material = models.CharField(
        max_length=20,
        choices=MATERIAL_CHOICES,
        default='ЛДСП',
        verbose_name="Материал"
    )
    thickness = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Толщина (мм)",
        help_text="Толщина в миллиметрах"
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Цвет/Оттенок"
    )
    price_per_square_meter = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за м²",
        help_text="Цена за квадратный метр"
    )

    def __str__(self):
        return f"{self.name} ({self.material}, {self.thickness}мм)"

    class Meta:
        verbose_name = "Плита"
        verbose_name_plural = "Плиты"
        ordering = ['material', 'thickness', 'name']

class Store(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название магазина")
    url_pattern = models.CharField(max_length=200, verbose_name="URL паттерн")
    price_selector = models.CharField(max_length=200, verbose_name="CSS селектор цены")
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Скидка магазина (%)",
        help_text="Процент скидки для этого магазина"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"


class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название бренда")
    description = models.TextField(blank=True, verbose_name="Описание")

    def get_mounting_types(self):
        return Product.objects.filter(brand=self).values_list('mounting_type', flat=True).distinct()

    def get_hinge_angles(self):
        return Product.objects.filter(brand=self).values_list('hinge_angle', flat=True).distinct()

    def get_hinge_closing_types(self):
        return Product.objects.filter(brand=self).values_list('hinge_closing_type', flat=True).distinct()

    def get_response_types(self):
        return Product.objects.filter(brand=self).values_list('response_type', flat=True).distinct()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название товара")

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Категория"
    )

    hinge_angle = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Угол открывания"
    )

    hinge_closing_type = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Тип закрывания"
    )

    runner_size = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Размер направляющих"
    )

    response_type=models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Тип ответки"
    )

    # Простое текстовое поле для типа
    mounting_type = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Тип"
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Бренд"
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
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Магазин"
    )
    last_parsed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последний парсинг"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Элемент"
        verbose_name_plural = "Элементы"


    @property
    def final_parsed_price(self):
        """Итоговая цена после применения скидки магазина"""
        if self.parsed_price and self.store and self.store.discount_percent:
            discount = self.parsed_price * (self.store.discount_percent / 100)
            return round(self.parsed_price - discount, 1)
        return round(self.parsed_price, 1) if self.parsed_price else 0

class Record(models.Model):
    STATUS_CHOICES = [
        ('otrisovka', 'Отрисовка'),
        ('zhdem_material', 'Ждем прибытия материала'),
        ('priekhal_v_ceh', 'Приехал в цех'),
        ('na_raspile', 'На распиле'),
        ('zakaz_gotov', 'Заказ готов'),
    ]
    
    created_at = models.DateTimeField(auto_now_add=True)
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
        verbose_name="Статус заказа"
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
    # Ручной ввод суммы для метода "погонный метр"
    designer_manual_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Зарплата проектировщика (пог. метр)"
    )
    # Отметки для распределения моржи
    margin_yura = models.BooleanField(default=True, verbose_name="Моржа Юра")
    margin_oleg = models.BooleanField(default=True, verbose_name="Моржа Олег")

    products = models.ManyToManyField(Product, related_name='records', blank=True, verbose_name="Комплектующие")
    plitas = models.ManyToManyField(
        Plita,
        through='RecordPlita',
        related_name='records',
        blank=True,
        verbose_name="Используемые плиты"
    )
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class RecordPlita(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    plita = models.ForeignKey(Plita, on_delete=models.CASCADE)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name="Количество (м²)",
        help_text="Количество в квадратных метрах"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Используемая плита"
        verbose_name_plural = "Используемые плиты"
        unique_together = ['record', 'plita']

    def __str__(self):
        return f"{self.record} - {self.plita} ({self.quantity}м²)"

class RecordProduct(models.Model):
    BUYER_CHOICES = [
        ('Юра', 'Юра'),
        ('Олег', 'Олег'),
    ]

    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
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
        verbose_name="Запись"
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
        verbose_name="Кто потратил"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.item} - {self.price} руб. ({self.spent_by})"

    class Meta:
        verbose_name = "Непланируемый расход"
        verbose_name_plural = "Непланируемые расходы"
        ordering = ['-created_at']