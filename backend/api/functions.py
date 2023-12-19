SHOPPING_LIST_TITLE_FOR_DOWNLOAD = shopping_list = (
    'Список покупок\n'
    'Пользователь: {user_full_name}\n')


def get_shopping_list_text(user, shopping_list_data):
    shopping_list = '\n'.join([
        f'{index}. {ingredient["amount"]} '
        f'({ingredient["ingredient__measurement_unit"]})'
        f'- {ingredient["ingredient__name"].capitalize()} '
        for index, ingredient in enumerate(shopping_list_data, start=1)
    ])
    return shopping_list
