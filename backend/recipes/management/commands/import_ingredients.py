import json
import sys

from django.core.management.base import BaseCommand

from ...models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из файла JSON'

    def handle(self, *args, **options):
        with open('./data/ingredients.json', 'r', encoding='utf-8') as file:
            ingredients = json.load(file)

        if Ingredient.objects.filter(id=1).exists():
            print('Ингредиенты уже есть в базе данных')
            sys.exit()
        for ingredient in ingredients:
            Ingredient.objects.create(**ingredient)

        self.stdout.write(self.style.SUCCESS(
            f'Импортировано {len(ingredients)} ингредиентов'))
