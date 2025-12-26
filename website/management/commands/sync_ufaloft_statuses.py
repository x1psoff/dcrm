from django.core.management.base import BaseCommand
from django.utils import timezone

import requests

from website.models import Record
from website.utils.ufaloft import (
    load_cookies,
    parse_dashboard,
    sync_by_index,
    DEFAULT_DASHBOARD_URL,
)


class Command(BaseCommand):
    help = 'Парсит lk.ufaloft.ru дашборд и синхронизирует статусы по индексу из заголовка (после "-")'

    def add_arguments(self, parser):
        parser.add_argument('--dashboard-url', default=DEFAULT_DASHBOARD_URL)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--index-field', default='first_name', choices=['first_name', 'last_name'], help='Поле записи, где хранится ваш индекс')
        parser.add_argument('--verbose', action='store_true', help='Печатать подробности сопоставления')

    def handle(self, *args, **options):
        session = requests.Session()
        if not load_cookies(session):
            self.stdout.write(self.style.ERROR('Нет сохранённых cookies. Сначала выполните ufaloft_login.'))
            return

        try:
            items = parse_dashboard(session, dashboard_url=options['dashboard_url'])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка загрузки дашборда: {e}'))
            return
        if options['verbose']:
            self.stdout.write(f'Найдено элементов на дашборде: {len(items)}')

        def update_record(my_index: str, mapped_status: str, raw_status: str, workshop_price: str) -> bool:
            try:
                idx = str(my_index).strip()
                # Выбранное поле
                field = options['index-field']
                q = {field: idx}
                record = Record.objects.filter(**q).first()
                # Fallback: попробовать другое поле, если не нашли
                if not record:
                    alt_field = 'last_name' if field == 'first_name' else 'first_name'
                    record = Record.objects.filter(**{alt_field: idx}).first()
                if not record:
                    if options['verbose']:
                        self.stdout.write(f'[MISS] index={idx} mapped={mapped_status} raw="{raw_status}" workshop_price="{workshop_price}"')
                    return False
                if options['dry_run']:
                    self.stdout.write(f"#{record.id} ({idx}): {record.status} -> {mapped_status or raw_status}, workshop_price: {workshop_price}")
                    return False
                changed = False
                if mapped_status and record.status != mapped_status:
                    record.status = mapped_status
                    changed = True
                
                # Обновляем стоимость работы цеха
                if workshop_price:
                    try:
                        # Парсим цену, убираем лишние символы
                        price_str = workshop_price.replace(' ', '').replace(',', '.')
                        # Извлекаем только числа
                        import re
                        price_match = re.search(r'(\d+(?:\.\d+)?)', price_str)
                        if price_match:
                            new_price = float(price_match.group(1))
                            if record.workshop_price != new_price:
                                record.workshop_price = new_price
                                changed = True
                    except (ValueError, TypeError):
                        if options['verbose']:
                            self.stdout.write(f"[WARNING] Не удалось распарсить цену цеха: {workshop_price}")
                
                # optionally store raw status somewhere if needed in future
                if changed:
                    record.save(update_fields=['status', 'workshop_price'])
                    if options['verbose']:
                        self.stdout.write(f"[UPDATED] #{record.id} ({idx}) -> {mapped_status}, workshop_price: {workshop_price}")
                return changed
            except Exception:
                return False

        updated = sync_by_index(update_record, items)
        self.stdout.write(self.style.SUCCESS(f'Готово. Обновлено записей: {updated}'))


