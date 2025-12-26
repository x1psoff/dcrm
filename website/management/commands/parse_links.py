from django.core.management.base import BaseCommand

from website.parsers import parse_links_file_and_save


class Command(BaseCommand):
    help = 'Читает ссылки из текстового файла и сохраняет товары (name из heading, тип закрывания и угол из detail-info-box)'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='parse_links.txt', help='Файл со ссылками (по одной на строку)')

    def handle(self, *args, **options):
        file_path = options['file']
        self.stdout.write(self.style.NOTICE(f'Чтение ссылок из: {file_path}'))
        count = parse_links_file_and_save(file_path=file_path)
        self.stdout.write(self.style.SUCCESS(f'Готово. Создано/обновлено: {count}'))


