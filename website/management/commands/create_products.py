from django.core.management.base import BaseCommand
from website.utils.product_generator import create_product_combinations


class Command(BaseCommand):
    help = 'Create all possible product combinations'

    def handle(self, *args, **options):
        created = create_product_combinations()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created} products')
        )