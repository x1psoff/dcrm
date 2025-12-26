from django.core.management.base import BaseCommand
from website.models import Record, Designer
from decimal import Decimal
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Списки для генерации случайных данных
FIRST_NAMES = [
    'Иван', 'Петр', 'Сергей', 'Александр', 'Дмитрий', 'Андрей', 'Михаил', 'Николай',
    'Алексей', 'Владимир', 'Олег', 'Юрий', 'Максим', 'Антон', 'Роман', 'Евгений',
    'Анна', 'Мария', 'Елена', 'Ольга', 'Татьяна', 'Наталья', 'Ирина', 'Светлана',
    'Екатерина', 'Надежда', 'Людмила', 'Валентина', 'Галина', 'Лариса'
]

LAST_NAMES = [
    'Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Соколов', 'Лебедев',
    'Новikov', 'Морозов', 'Петров', 'Волков', 'Соловьев', 'Васильев', 'Зайцев', 'Павлов',
    'Семенов', 'Голубев', 'Виноградов', 'Богданов', 'Воробьев', 'Федоров', 'Михайлов',
    'Белов', 'Тарасов', 'Беляев', 'Комаров', 'Орлов', 'Киселев', 'Макаров'
]

CITIES = [
    'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 'Нижний Новгород',
    'Челябинск', 'Самара', 'Омск', 'Ростов-на-Дону', 'Уфа', 'Красноярск', 'Воронеж',
    'Пермь', 'Волгоград', 'Краснодар', 'Саратов', 'Тюмень', 'Тольятти', 'Ижевск'
]

STATUSES = [
    'otrisovka',
    'zhdem_material',
    'priekhal_v_ceh',
    'na_raspile',
    'zakaz_gotov'
]


class Command(BaseCommand):
    help = 'Create 100 test records for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of records to create (default: 100)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Получаем всех дизайнеров (если есть)
        designers = list(Designer.objects.all())
        
        # Генерируем записи
        created_count = 0
        now = timezone.now()
        
        # Распределяем записи по месяцам (последние 3 месяца)
        for i in range(count):
            # Случайная дата в последние 3 месяца
            days_ago = random.randint(0, 90)
            created_at = now - timedelta(days=days_ago)
            
            # Случайные данные
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            status = random.choice(STATUSES)
            
            # Случайная сумма договора (от 50000 до 500000)
            contract_amount = Decimal(random.randint(50000, 500000))
            
            # Случайный аванс (от 10% до 50% от суммы договора)
            advance_percent = random.randint(10, 50)
            advance = contract_amount * Decimal(advance_percent) / 100
            
            # Случайный телефон
            phone = f"+7{random.randint(9000000000, 9999999999)}"
            
            # Случайный город
            city = random.choice(CITIES)
            
            # Случайный адрес
            address = f"ул. {random.choice(['Ленина', 'Пушкина', 'Гагарина', 'Мира', 'Советская'])} д. {random.randint(1, 100)}"
            
            # Случайный telegram (50% вероятность)
            telegram = ''
            if random.random() > 0.5:
                telegram = f"@{first_name.lower()}_{random.randint(100, 999)}"
            
            # Случайный дизайнер (если есть)
            designer = random.choice(designers) if designers else None
            
            # Создаем запись
            record = Record.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                telegram=telegram,
                address=address,
                city=city,
                status=status,
                contract_amount=contract_amount,
                advance=advance,
                designer=designer,
                margin_yura=random.choice([True, False]),
                margin_oleg=random.choice([True, False]),
            )
            
            # Устанавливаем дату создания вручную (так как auto_now_add не позволяет)
            Record.objects.filter(id=record.id).update(created_at=created_at)
            
            created_count += 1
            
            if created_count % 10 == 0:
                self.stdout.write(f'Created {created_count} records...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} test records')
        )

