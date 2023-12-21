# Generated by Django 3.2.16 on 2023-12-21 10:39

from django.db import migrations, models
import recipes.validators


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_subscription_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=200, unique=True, verbose_name='e-mail'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(db_index=True, max_length=150, unique=True, validators=[recipes.validators.validate_username], verbose_name='Никнэйм'),
        ),
    ]
