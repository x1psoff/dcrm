from django.core.management.base import BaseCommand

import requests

from website.utils.ufaloft import login_with_credentials, save_cookies, DEFAULT_LOGIN_URL


class Command(BaseCommand):
    help = 'Вход в lk.ufaloft.ru и сохранение cookies для последующего парсинга (учитывает 2FA через --otp)'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--otp', required=False, help='Код подтверждения из WhatsApp (если требуется)')
        parser.add_argument('--login-url', default=DEFAULT_LOGIN_URL)

    def handle(self, *args, **options):
        session = requests.Session()
        login_with_credentials(
            session=session,
            username=options['username'],
            password=options['password'],
            login_url=options['login_url'],
            otp_code=options.get('otp'),
        )
        save_cookies(session)
        self.stdout.write(self.style.SUCCESS('Куки сохранены. Теперь можно запускать синхронизацию.'))


