import json

from django.conf import settings
from django.core.management.base import BaseCommand

from ...models import Tag


class Command(BaseCommand):
    help = 'Импорт тэгов из файла JSON'

    def handle(self, *args, **options):
        with open(
            f'{settings.FOLDER_FOR_IMPORT}/tags.json',
            'r',
            encoding='utf-8'
        ) as file:
            tags = json.load(file)
        tags_amount_before = Tag.objects.count()
        Tag.objects.bulk_create(
            (Tag(**tag) for tag in tags),
            ignore_conflicts=True
        )
        self.stdout.write(self.style.SUCCESS(
            f'Импортировано {Tag.objects.count()-tags_amount_before} тэгов'))
