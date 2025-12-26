from django.core.management.base import BaseCommand
from website.models import Record, Designer
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.db import transaction


class Command(BaseCommand):
    help = 'Создает 2 тестовых заказа за 2024 год'

    def handle(self, *args, **options):
        # Получаем первого доступного дизайнера (если есть)
        designer = Designer.objects.first()
        
        # Создаем записи за 2024 год
        records_data = [
            {
                'first_name': 'Иван',
                'last_name': 'Петров',
                'phone': '+79991234567',
                'telegram': '@ivan_petrov',
                'address': 'ул. Ленина д. 10',
                'city': 'Москва',
                'status': 'zakaz_gotov',
                'contract_amount': Decimal('250000.00'),
                'advance': Decimal('50000.00'),
                'designer': designer,
                'margin_yura': True,
                'margin_oleg': False,
                'created_at': datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.get_current_timezone())
            },
            {
                'first_name': 'Мария',
                'last_name': 'Иванова',
                'phone': '+79997654321',
                'telegram': '@maria_ivanova',
                'address': 'ул. Пушкина д. 25',
                'city': 'Санкт-Петербург',
                'status': 'otrisovka',
                'contract_amount': Decimal('180000.00'),
                'advance': Decimal('36000.00'),
                'designer': designer,
                'margin_yura': False,
                'margin_oleg': True,
                'created_at': datetime(2024, 9, 20, 14, 15, 0, tzinfo=timezone.get_current_timezone())
            }
        ]
        
        created_count = 0
        
        with transaction.atomic():
            for record_data in records_data:
                # Создаем запись
                record = Record.objects.create(
                    first_name=record_data['first_name'],
                    last_name=record_data['last_name'],
                    phone=record_data['phone'],
                    telegram=record_data['telegram'],
                    address=record_data['address'],
                    city=record_data['city'],
                    status=record_data['status'],
                    contract_amount=record_data['contract_amount'],
                    advance=record_data['advance'],
                    designer=record_data['designer'],
                    margin_yura=record_data['margin_yura'],
                    margin_oleg=record_data['margin_oleg'],
                )
                
                # Устанавливаем дату создания вручную
                Record.objects.filter(id=record.id).update(created_at=record_data['created_at'])
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создана запись {created_count}: {record.first_name} {record.last_name} '
                        f'(ID: {record.id}, Дата: {record_data["created_at"].strftime("%d.%m.%Y")})'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nУспешно создано {created_count} записей за 2024 год')
        )

