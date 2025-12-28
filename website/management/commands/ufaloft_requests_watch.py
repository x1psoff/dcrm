import time

import requests
from django.core.management.base import BaseCommand

from website.utils.ufaloft import (
    DEFAULT_DASHBOARD_URL,
    load_cookies,
    parse_dashboard,
    sync_by_index,
    map_external_status_to_local,
    parse_workshop_price,
)
from website.models import Record


class Command(BaseCommand):
    help = 'Без браузера: каждые N минут парсит UFALOFT дашборд через requests+cookies и обновляет статусы/стоимость.'

    def add_arguments(self, parser):
        parser.add_argument('--dashboard-url', default=DEFAULT_DASHBOARD_URL)
        parser.add_argument('--interval-min', type=int, default=60)
        parser.add_argument('--index-field', default='first_name', choices=['first_name', 'last_name'])
        parser.add_argument('--verbose', action='store_true')

    def handle(self, *args, **options):
        dashboard_url = options['dashboard_url']
        interval_sec = max(60, options['interval_min'] * 60)

        session = requests.Session()
        if not load_cookies(session):
            self.stdout.write(self.style.ERROR('Нет сохранённых cookies. Сначала выполните: python manage.py ufaloft_login --username ... --password ... --otp ...'))
            return

        def update_record(my_index: str, mapped_status: str, raw_status: str, workshop_price: str) -> bool:
            idx = str(my_index).strip()
            field = options['index_field']
            record = Record.objects.filter(**{field: idx}).first()
            if not record:
                alt_field = 'last_name' if field == 'first_name' else 'first_name'
                record = Record.objects.filter(**{alt_field: idx}).first()
            if not record:
                if options['verbose']:
                    self.stdout.write(f'[MISS] index={idx} mapped={mapped_status} raw="{raw_status}" workshop_price="{workshop_price}"')
                return False

            if not mapped_status:
                mapped_status = map_external_status_to_local(raw_status)

            changed = False
            if mapped_status and record.status != mapped_status:
                record.status = mapped_status
                changed = True

            if workshop_price:
                try:
                    new_price = parse_workshop_price(workshop_price)
                    if new_price is not None and record.workshop_price != new_price:
                        record.workshop_price = new_price
                        changed = True
                except Exception:
                    if options['verbose']:
                        self.stdout.write(f"[WARNING] Не удалось распарсить цену цеха: {workshop_price}")

            if changed:
                record.save(update_fields=['status', 'workshop_price'])
                if options['verbose']:
                    self.stdout.write(f'[UPDATED] #{record.id} ({idx}) -> {mapped_status}, workshop_price: {record.workshop_price}')

            return changed

        self.stdout.write(self.style.SUCCESS('UFALOFT requests-watch запущен. Для остановки: Ctrl+C'))
        while True:
            try:
                items = parse_dashboard(session, dashboard_url=dashboard_url)
                updated = sync_by_index(update_record, items)
                self.stdout.write(self.style.SUCCESS(f'Синхронизация завершена. Обновлено: {updated}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка синхронизации: {e}'))
            time.sleep(interval_sec)


