from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    ShoppingList,
    Subscription,
    Tag,
    User,
)


admin.site.empty_value_display = 'Не задано'


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'is_staff',
        'first_name',
        'last_name',
    )
    search_fields = (
        'email',
        'username',
        'is_staff',
        'first_name',
        'last_name',
    )


class RecipeIngredientInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 10
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'text',
        'cooking_time',
        'pub_date',
    )
    list_filter = ('name', 'author__username', 'tags__name', 'cooking_time')
    inlines = (RecipeIngredientInLine,)
    search_fields = ('name', 'author__username',)


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
admin.site.register(RecipeTag, RecipeTagAdmin)
admin.site.register(ShoppingList, FavoriteShoppingListAdmin)
admin.site.register(Subscription, SubscribtionAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(User, UserAdmin)
