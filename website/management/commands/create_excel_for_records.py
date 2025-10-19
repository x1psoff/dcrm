from django.core.management.base import BaseCommand
from website.models import Record, RecordExcelFile
import os
import shutil
from django.conf import settings


class Command(BaseCommand):
    help = 'Create Excel files for all existing records'

    def handle(self, *args, **options):
        records = Record.objects.all()

        for record in records:
            # Проверяем, есть ли уже файл
            if not RecordExcelFile.objects.filter(record=record).exists():
                try:
                    template_path = os.path.join(settings.MEDIA_ROOT, 'excel_templates', 'комплектация_Кухни.xlsx')

                    if not os.path.exists(template_path):
                        # Если шаблона нет, создаем пустой файл
                        import openpyxl
                        wb = openpyxl.Workbook()
                        template_path = os.path.join(settings.MEDIA_ROOT, 'excel_templates', 'empty_template.xlsx')
                        os.makedirs(os.path.dirname(template_path), exist_ok=True)
                        wb.save(template_path)

                    # Создаем путь для файла записи
                    record_excel_path = os.path.join(settings.MEDIA_ROOT, 'records_excel', f'record_{record.id}.xlsx')
                    os.makedirs(os.path.dirname(record_excel_path), exist_ok=True)

                    # Копируем шаблон
                    shutil.copy2(template_path, record_excel_path)

                    # Создаем запись в базе
                    RecordExcelFile.objects.create(
                        record=record,
                        excel_file=f'records_excel/record_{record.id}.xlsx'
                    )

                    self.stdout.write(self.style.SUCCESS(f'Created Excel for record {record.id}'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating Excel for record {record.id}: {str(e)}'))