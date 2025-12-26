from django.core.management.base import BaseCommand

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from website.utils.ufaloft import save_cookies, DEFAULT_LOGIN_URL


class Command(BaseCommand):
    help = 'Открывает браузер для ручного входа в lk.ufaloft.ru; после входа сохраняет cookies для автопарсинга.'

    def add_arguments(self, parser):
        parser.add_argument('--url', default=DEFAULT_LOGIN_URL, help='Стартовый URL (страница входа/дашборд)')
        parser.add_argument('--wait-sec', type=int, default=240, help='Максимум секунд ожидания входа')

    def handle(self, *args, **options):
        start_url = options['url']
        wait_sec = options['wait_sec']

        self.stdout.write('Открываю браузер. Выполните вход и подтвердите 2FA (WhatsApp).')

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Используем встроенный Selenium Manager (автоматически найдет правильный ChromeDriver)
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(start_url)

            # Условие успешного входа: появятся строки таблицы или исчезнет форма логина
            wait = WebDriverWait(driver, wait_sec)
            try:
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.listing-table-tr')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.listing-table-tr.unread-item-row')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table.table-striped.table-bordered.table-hover')),
                    )
                )
            except Exception:
                self.stdout.write(self.style.WARNING('Таймаут ожидания. Попытаюсь всё равно сохранить куки.'))

            # Сохраняем куки selenium -> requests -> файл
            session = requests.Session()
            for c in driver.get_cookies():
                # c: {name, value, domain, path, expiry, secure, httpOnly}
                session.cookies.set(c['name'], c['value'], domain=c.get('domain'), path=c.get('path', '/'))

            save_cookies(session)
            self.stdout.write(self.style.SUCCESS('Куки сохранены. Можно закрывать браузер и запускать синхронизацию.'))
        finally:
            try:
                driver.quit()
            except Exception:
                pass


