from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    is_favorited = filters.CharFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.CharFilter(
        method='get_is_in_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    def get_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoppinglists__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags')
