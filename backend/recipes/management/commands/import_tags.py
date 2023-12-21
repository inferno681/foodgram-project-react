import json
import sys

from django.core.management.base import BaseCommand

from ...models import Tag


class Command(BaseCommand):
    help = 'Импорт тэгов из файла JSON'

    def handle(self, *args, **options):
        with open('./data/tags.json', 'r', encoding='utf-8') as file:
            tags = json.load(file)

        if Tag.objects.filter(id=1).exists():
            print('Тэги уже есть в базе данных')
            sys.exit()
        for tag in tags:
            Tag.objects.create(**tag)

        self.stdout.write(self.style.SUCCESS(
            f'Импортировано {len(tags)} тэгов'))
