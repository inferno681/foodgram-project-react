import json

from django.core.management.base import BaseCommand

from ...models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из файла JSON'

    def handle(self, *args, **options):
        with open('./data/ingredients.json', 'r', encoding='utf-8') as file:
            ingredients = json.load(file)
        ingredients_for_upload = [
            ingredient for ingredient in ingredients if ingredient['name'] in (
                set([ingredient['name'] for ingredient in ingredients])
            ).difference(set(Ingredient.objects.values_list('name', flat=True)
                             ))]
        Ingredient.objects.bulk_create(Ingredient(
            **ingredient) for ingredient in ingredients_for_upload)

        self.stdout.write(self.style.SUCCESS(
            f'Импортировано {len(ingredients_for_upload)} ингредиентов'))
