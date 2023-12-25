import json

from django.conf import settings
from django.core.management.base import BaseCommand

from ...models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из файла JSON'

    def handle(self, *args, **options):
        with open(
            f'{settings.FOLDER_FOR_IMPORT}ingredients.json',
            'r',
            encoding='utf-8',
        ) as file:
            ingredients = json.load(file)
        ingrediens_amount_before = Ingredient.objects.count()
        Ingredient.objects.bulk_create((
            Ingredient(**ingredient)
            for ingredient in ingredients),
            ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(
            'Импортировано '
            f'{Ingredient.objects.count()-ingrediens_amount_before} '
            'ингредиентов'))
