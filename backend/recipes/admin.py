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


class RecipeTagInLine(admin.TabularInline):
    extra = 5
    min_num = 1


class RecipesCookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        return (
            ('fast', 'быстрые (до 15 минут)'),
            ('medium', 'средние (от 15 до 30 минут)'),
            ('long', 'долгие (более 30 минут)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return Recipe.objects.filter(cooking_time__lt=15)
        if self.value() == 'medium':
            return Recipe.objects.filter(cooking_time__range=(15, 30))
        if self.value() == 'long':
            return Recipe.objects.filter(cooking_time__gte=30)
        return queryset


class AuthorFilter(admin.SimpleListFilter):
    title = 'Автор'
    parameter_name = 'author'

    def lookups(self, request, model_admin):
        return sorted(set((recipe.author.id, recipe.author.username)
                          for recipe in model_admin.model.objects.all()
                          ),  key=lambda x: x[1])

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(author__id=self.value())
        return queryset


class TagFilter(admin.SimpleListFilter):
    title = 'Тэг'
    parameter_name = 'tag'

    def lookups(self, request, model_admin):
        return (
            (tag.id, tag.name)
            for tag in Tag.objects.all()
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__id=self.value())
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
    list_filter = (AuthorFilter, TagFilter, RecipesCookingTimeFilter)
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
            f'{tag.color}">{tag}</span>'
            for tag in recipe.tags.all()
        )

    @display(description='Ингредиенты')
    @mark_safe
    def show_ingredients(self, recipe):
        return '<br> '.join(
            f'{ingredient["amount"]} '
            f'{ingredient["ingredient__measurement_unit"]} '
            f'{ingredient["ingredient__name"]:.50}'
            for ingredient in recipe.recipes.values(
                'amount', 'ingredient__measurement_unit', 'ingredient__name'
            )
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
