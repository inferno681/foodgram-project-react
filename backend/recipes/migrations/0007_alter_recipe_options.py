# Generated by Django 3.2.16 on 2023-12-25 16:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_ingredient_unique_name_measurement_unit'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={'default_related_name': 'recipes', 'ordering': ('-pub_date',), 'verbose_name': 'Рецепт', 'verbose_name_plural': 'Рецепты'},
        ),
    ]