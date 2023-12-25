from recipes.models import ShoppingList


def get_shopping_list_text(user):
    return '\n'.join([
        'Список покупок',
        'Пользователь: {user_full_name}'.format(
            user_full_name=user.get_full_name()
        ), *[
            f'{index}. {ingredient["amount"]} '
            f'({ingredient["ingredient__measurement_unit"]}) '
            f'- {ingredient["ingredient__name"]:.50} '
            for index, ingredient in enumerate(
                ShoppingList().get_shopping_list_ingredients(user),
                start=1
            )
        ], 'Список рецептов: ',
        *[f'{index}. {recipe:.50}' for index, recipe in enumerate(
            ShoppingList().get_shopping_list_recipes(user), start=1)
          ]])
