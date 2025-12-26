import time

from django.core.management.base import BaseCommand

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from website.models import Record
from website.utils.ufaloft import DEFAULT_DASHBOARD_URL, map_external_status_to_local, sync_by_index
from website.utils.ufaloft_selenium import parse_dashboard_with_driver


class Command(BaseCommand):
    help = 'Открывает браузер (не закрывает) и каждые N минут парсит дашборд, обновляя статусы по индексу.'

    def add_arguments(self, parser):
        parser.add_argument('--dashboard-url', default=DEFAULT_DASHBOARD_URL)
        parser.add_argument('--interval-min', type=int, default=60)
        parser.add_argument('--index-field', default='first_name', choices=['first_name', 'last_name'])
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('--headless', action='store_true', help='Run Chrome in headless mode (no GUI)')

    def handle(self, *args, **options):
        dashboard_url = options['dashboard_url']
        interval_sec = max(60, options['interval_min'] * 60)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        if options.get('headless'):
            chrome_options.add_argument('--headless')
            self.stdout.write('Запускаю Chrome в headless режиме...')
        else:
            self.stdout.write('Открываю Chrome браузер...')

        try:
            # Используем встроенный Selenium Manager (автоматически найдет правильный ChromeDriver)
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка запуска Chrome: {e}'))
            self.stdout.write('Попробуйте запустить с --headless или установите ChromeDriver')
            return
        self.stdout.write('Открыл браузер. Выполните вход и 2FA, табличные строки появятся автоматически.')
        driver.get(dashboard_url)

        try:
            WebDriverWait(driver, 600).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.listing-table-tr')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.listing-table-tr.unread-item-row')),
                )
            )
        except Exception:
            self.stdout.write(self.style.WARNING('Таблица не появилась за 10 минут. Продолжаю наблюдение.'))

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
            
            if changed:
                record.save(update_fields=['status', 'workshop_price'])
                if options['verbose']:
                    self.stdout.write(f'[UPDATED] #{record.id} ({idx}) -> {mapped_status}, workshop_price: {workshop_price}')
            return changed

        try:
            while True:
                try:
                    items = parse_dashboard_with_driver(driver)
                    updated = sync_by_index(update_record, items)
                    self.stdout.write(self.style.SUCCESS(f'Синхронизация завершена. Обновлено: {updated}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Ошибка синхронизации: {e}'))
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            self.stdout.write('Останавливаю наблюдатель...')
        finally:
            try:
                # По просьбе оставить браузер открытым можно закомментировать quit
                pass
            except Exception:
                pass


