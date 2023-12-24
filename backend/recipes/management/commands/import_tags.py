import json

from django.core.management.base import BaseCommand

from ...models import Tag


class Command(BaseCommand):
    help = 'Импорт тэгов из файла JSON'

    def handle(self, *args, **options):
        with open('./data/tags.json', 'r', encoding='utf-8') as file:
            tags = json.load(file)
        tags_for_upload = [
            tag for tag in tags if tag['slug'] in (
                set([tag['slug'] for tag in tags]).difference(
                    set(Tag.objects.values_list('slug', flat=True)
                        )))]
        Tag.objects.bulk_create(Tag(
            **tag) for tag in tags_for_upload)

        self.stdout.write(self.style.SUCCESS(
            f'Импортировано {len(tags_for_upload)} тэгов'))
