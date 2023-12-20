from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin

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


class SubscriptionsAmountFilter(admin.SimpleListFilter):
    title = 'Количество подписок'
    parameter_name = 'subscriptions_amount'

    def lookups(self, request, model_admin):
        return (
            ('gt_zero', 'Больше нуля'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'gt_zero':
            return User.subscriptions_as_user.
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
    list_filter = [SubscriptionsAmountFilter]

    @display(description='Количество рецептов')
    def recipes_amount(self, obj):
        return obj.recipes.count()

    @display(description='Количество подписок')
    def subscriptions_amount(self, obj):
        return obj.subscriptions_as_user.count()

    @display(description='Количество подписчиков')
    def subscribers_amount(self, obj):
        return obj.subscriptions.count()


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 5
    min_num = 1


class RecipeTagInLine(admin.TabularInline):
    extra = 5
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'text',
        'cooking_time',
        'added_to_favorites',
        'pub_date',
    )
    list_filter = ('name', 'author__username', 'tags__name', 'cooking_time')
    readonly_fields = ('added_to_favorites',)
    inlines = (RecipeIngredientInLine, )
    search_fields = ('name', 'author__username',)

    @display(description='В избранном у')
    def added_to_favorites(self, obj):
        return obj.favorites.count()


class FavoriteShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name', 'measurement_unit',)
    search_fields = ('name', 'measurement_unit',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    list_filter = ('name', 'color', 'slug',)
    search_fields = ('name', 'slug',)


class SubscribtionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
    list_filter = ('user', 'author',)
    search_fields = ('user', 'author',)


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient',)
    list_filter = ('recipe',)


class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag',)
    list_filter = ('recipe',)


admin.site.register(Favorite, FavoriteShoppingListAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(ShoppingList, FavoriteShoppingListAdmin)
admin.site.register(Subscription, SubscribtionAdmin)
admin.site.register(Tag, TagAdmin)
