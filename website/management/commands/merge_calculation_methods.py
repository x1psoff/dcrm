from django.core.management.base import BaseCommand
from django.db import transaction
from website.models import CalculationMethod, Designer


class Command(BaseCommand):
    help = 'Объединяет дублирующиеся методы расчета зарплаты'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Находим методы расчета
            try:
                pogonny_metr = CalculationMethod.objects.get(name='Погонный метр')
                kvadratny_metr = CalculationMethod.objects.get(name='За квадратный метр')
                
                self.stdout.write(f'Найден "Погонный метр" (ID: {pogonny_metr.id})')
                self.stdout.write(f'Найден "За квадратный метр" (ID: {kvadratny_metr.id})')
                
                # Находим всех рабочих, использующих "За квадратный метр"
                designers_using_kvadratny = Designer.objects.filter(method=kvadratny_metr)
                count = designers_using_kvadratny.count()
                
                if count > 0:
                    self.stdout.write(f'Найдено {count} рабочих, использующих "За квадратный метр"')
                    
                    # Переводим их на "Погонный метр"
                    designers_using_kvadratny.update(method=pogonny_metr)
                    self.stdout.write('Все рабочие переведены на "Погонный метр"')
                
                # Удаляем дублирующий метод
                kvadratny_metr.delete()
                self.stdout.write('Метод "За квадратный метр" удален')
                
                self.stdout.write(
                    self.style.SUCCESS('Успешно объединены методы расчета!')
                )
                
            except CalculationMethod.DoesNotExist as e:
                self.stdout.write(
                    self.style.WARNING(f'Метод не найден: {e}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка: {e}')
                )
