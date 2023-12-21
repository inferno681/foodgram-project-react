SHOPPING_LIST_TITLE_FOR_DOWNLOAD = shopping_list = (
    'Список покупок\n'
    'Пользователь: {user_full_name}\n')


def get_shopping_list_text(user, ingredients, recipes):
    shopping_list = '\n'.join([
        'Список покупок',
        'Пользователь: {user_full_name}'.format(
            user_full_name=user.get_full_name()
        ), *[
            f'{index}. {ingredient["amount"]} '
            f'({ingredient["ingredient__measurement_unit"]}) '
            f'- {ingredient["ingredient__name"]:.50} '
            for index, ingredient in enumerate(ingredients, start=1)
        ], 'Список рецептов: ',
        *[f'{index}. {recipe:.50}' for index, recipe in enumerate(
            recipes, start=1)
          ]])
    return shopping_list
