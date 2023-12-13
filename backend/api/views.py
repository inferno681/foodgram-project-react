from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from .filters import RecipeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Subscription,
    Tag,
    User,
)
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer
)


NO_RECIPE_MESSAGE = {'errors': 'Нет такого рецепта'}
RECIPE_IN_SHOPPING_LIST_MESSAGE = {'errors': 'Рецепт уже в списке покупок!'}
NO_RECIPE_IN_SHOPPING_LIST_MESSAGE = {
    'errors': 'Рецепта нет в списке покупок!'}


class TagIngredientViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    pagination_class = None


class TagViewSet(TagIngredientViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(TagIngredientViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=('POST', 'DELETE'),
            detail=True,
            url_path='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        user = request.user
        if request.method == 'POST':
            if not Recipe.objects.filter(id=pk).exists():
                raise ValidationError(NO_RECIPE_MESSAGE)
            recipe = Recipe.objects.filter(id=pk).get()
            shopping_list, created = ShoppingList.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                raise ValidationError(RECIPE_IN_SHOPPING_LIST_MESSAGE)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe = get_object_or_404(Recipe, id=pk)
        if not ShoppingList.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(NO_RECIPE_IN_SHOPPING_LIST_MESSAGE)
        ShoppingList.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',),
            detail=False,
            url_path='download_shopping_cart',
            permission_classes=(IsAuthenticated,))
    def download_shopping_list(self, request):
        user = request.user
        if not ShoppingList.objects.filter(user=user).exists():
            raise ValidationError(
                {'errors': 'Список покупок пуст!'})
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppinglists__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        shopping_list = ('Список покупок\n'
                         f'Пользователь: {user.get_full_name()}\n')
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(methods=('POST', 'DELETE'),
            detail=True,
            url_path='favorite',
            permission_classes=(IsAuthenticated,))
    def favorites(self, request, pk):
        user = request.user
        if request.method == 'POST':
            if not Recipe.objects.filter(id=pk).exists():
                raise ValidationError(
                    {'errors': 'Нет такого рецепта'})
            recipe = Recipe.objects.filter(id=pk).get()
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                raise ValidationError(
                    {'errors': 'Рецепт уже в избранном!'})
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe = get_object_or_404(Recipe, id=pk)
        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                {'errors': 'Рецепта нет в избранном!'})
        Favorite.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    @action(methods=('POST', 'DELETE'),
            detail=True,
            url_path='subscribe',
            permission_classes=(IsAuthenticated,))
    def subscribtion(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            raise ValidationError(
                {'errors': 'Нельзя подписаться на себя!'})
        if request.method == 'POST':
            subscribtion, created = Subscription.objects.get_or_create(
                user=user, author=author)
            if not created:
                raise ValidationError(
                    {'errors': 'Автор уже в избранном!'})
            serializer = SubscriptionSerializer(
                subscribtion, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                {'errors': 'Нельзя удалить несуществующую подписку!'})
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',),
            detail=False,
            url_path='subscriptions',
            permission_classes=(IsAuthenticated,))
    def get_subscribtions(self, request):
        bloger = request.user.subscriber.all()
        pages = self.paginate_queryset(bloger)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
