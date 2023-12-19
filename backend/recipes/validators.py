import re

from django.core.exceptions import ValidationError


INVALID_USERNAME_MESSAGE = ('Имя пользователя содержит недопустимые символы: '
                            '{invalid_symbols}.')
INVALID_COLOR_MESSAGE = 'Задайте цвет в HEX формате!'


def validate_username(username):
    invalid_symbols = re.findall(r'[^\w@.+-]', username)
    if invalid_symbols:
        raise ValidationError(
            INVALID_USERNAME_MESSAGE.format(
                invalid_symbols="".join(set(invalid_symbols)))
        )
    return username


def validate_color(color):
    if not re.search(r'^#([0-9a-fA-F]{6})$', color):
        raise ValidationError(
            INVALID_COLOR_MESSAGE)
    return color
