import ast

from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Subscription,
    Tag,
    User,
)


admin.site.empty_value_display = 'Не задано'
admin.site.unregister(Group)


class SubscriptionsExistenceFilter(admin.SimpleListFilter):
    title = 'С учетом подписок'
    parameter_name = 'subscriptions_amount'

    def lookups(self, request, model_admin):
        return (
            ('with_subscriptions', 'с подписками'),
            ('with_subscribers', 'с подписчиками'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with_subscriptions':
            return User.objects.filter(
                subscriptions_as_user__isnull=False).distinct()
        if self.value() == 'with_subscribers':
            return User.objects.filter(
                subscriptions__isnull=False).distinct()
        return queryset


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'email',
        'username',
        'is_staff',
        'first_name',
        'last_name',
        'recipes_amount',
        'subscriptions_amount',
        'subscribers_amount'
    )
    readonly_fields = (
        'recipes_amount',
        'subscriptions_amount',
        'subscribers_amount')
    search_fields = (
        'email',
        'username',
        'is_staff',
        'first_name',
        'last_name',
    )
    list_filter = (SubscriptionsExistenceFilter,)

    @display(description='Рецептов')
    def recipes_amount(self, user):
        return user.recipes.count()

    @display(description='Подписок')
    def subscriptions_amount(self, user):
        return user.subscriptions_as_user.count()

    @display(description='Подписчиков')
    def subscribers_amount(self, user):
        return user.subscriptions.count()


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 5
    min_num = 1


class RecipesCookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        cooking_times_data = [
            recipe.cooking_time for recipe in Recipe.objects.all()
        ]
        step = (max(cooking_times_data) - min(cooking_times_data)) / 3
        if step == 0:
            return None
        bin_points = [round(min(cooking_times_data) + i * step)
                      for i in range(4)]
        bin_points[0] = 0
        recipes_counts = [
            sum(1 for value in cooking_times_data
                if bin_points[i] < value <= bin_points[i + 1])
            for i in range(3)
        ]

        return (
            ((bin_points[0], bin_points[1]),
             'быстрые (до '
             f'{bin_points[1]} минут)'
             f'(Рецептов:{recipes_counts[0]}) '),
            ((bin_points[1]+1, bin_points[2]),
             'средние ('
             f'от {bin_points[1]} '
             f'до {bin_points[2]} минут) '
             f'(Рецептов:{recipes_counts[1]})'),
            ((bin_points[2]+1, bin_points[3]),
             f'долгие (более {bin_points[2]} минут) '
             f'(Рецептов:{recipes_counts[2]})'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return Recipe.objects.filter(
                cooking_time__range=ast.literal_eval(self.value()))
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'text',
        'cooking_time',
        'show_tags',
        'show_ingredients',
        'added_to_favorites',
        'image_preview',
        'pub_date',
    )
    list_filter = (('author', admin.filters.RelatedOnlyFieldListFilter),
                   ('tags', admin.filters.RelatedOnlyFieldListFilter),
                   RecipesCookingTimeFilter)
    readonly_fields = ('added_to_favorites', 'show_tags',
                       'show_ingredients', 'image_preview')
    inlines = (RecipeIngredientInLine, )
    search_fields = ('name', 'author__username', 'tags__name', 'tags__slug')

    @display(description='Изображение')
    @mark_safe
    def image_preview(self, recipe):
        return f'<img src="{recipe.image.url}" width="150" height="150" />'

    @display(description='В избранном у')
    def added_to_favorites(self, recipe):
        return recipe.favorites.count()

    @display(description='Тэги')
    @mark_safe
    def show_tags(self, recipe):
        return '<br> '.join(
            '<span style="background-color: '
            f'{tag.color}">{tag.name}</span>'
            for tag in recipe.tags.all()
        )

    @display(description='Ингредиенты')
    @mark_safe
    def show_ingredients(self, recipe):
        return '<br> '.join(
            f'{ingredient.amount} '
            f'{ingredient.ingredient.measurement_unit} '
            f'{ingredient.ingredient.name:.50}'
            for ingredient in recipe.recipeingredients.all()
        )


@admin.register(Favorite, ShoppingList)
class FavoriteShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('measurement_unit',)
    search_fields = ('name', 'measurement_unit',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    search_fields = ('name', 'slug',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
    list_filter = ('user', 'author',)
    search_fields = ('user', 'author',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient',)
    list_filter = ('recipe',)
