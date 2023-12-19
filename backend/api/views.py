from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    SAFE_METHODS
)
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
from .pagination import LimitPageNumberPagination
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
SHOPPING_LIST_EMPTY_MESSAGE = {'errors': 'Список покупок пуст!'}
SHOPPING_LIST_TITLE_FOR_DOWNLOAD = shopping_list = (
    'Список покупок\n'
    'Пользователь: {user_full_name}\n')
SHOPPING_LIST_FILE_NAME = '{username}_shopping_list.txt'
RECIPE_IN_FAVORITES_MESSAGE = {'errors': 'Рецепт уже в избранном!'}
NO_RECIPE_IN_FAVORITE_MESSAGE = {'errors': 'Рецепта нет в избранном!'}
SELF_SUBSCRIBE_MESSAGE = {'errors': 'Нельзя подписаться на себя!'}
SUBSCRIPTION_EXIST_MESSAGE = {'errors': 'Вы уже подписаны на этого автора!'}
NO_SUBSCRIBTION_MESSAGE = {'errors': 'Нельзя удалить несуществующую подписку!'}


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
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
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            shopping_list, created = ShoppingList.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                raise ValidationError(RECIPE_IN_SHOPPING_LIST_MESSAGE)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(ShoppingList, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',),
            detail=False,
            url_path='download_shopping_cart',
            permission_classes=(IsAuthenticated,))
    def download_shopping_list(self, request):
        user = request.user
        if not ShoppingList.objects.filter(user=user).exists():
            raise ValidationError(SHOPPING_LIST_EMPTY_MESSAGE)
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppinglists__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        shopping_list = SHOPPING_LIST_TITLE_FOR_DOWNLOAD.format(
            user_full_name=user.get_full_name()
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        filename = SHOPPING_LIST_FILE_NAME.format(username=user.username)
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
                raise ValidationError(NO_RECIPE_MESSAGE)
            recipe = Recipe.objects.filter(id=pk).get()
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                raise ValidationError(RECIPE_IN_FAVORITES_MESSAGE)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe = get_object_or_404(Recipe, id=pk)
        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(NO_RECIPE_IN_FAVORITE_MESSAGE)
        Favorite.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    def get_permissions(self):
        if self.request.path == '/api/users/me/':
            permission_classes = (IsAuthenticated,)
        elif self.action == 'subscribtion':
            permission_classes = (IsAuthenticated,)
        else:
            permission_classes = (AllowAny,)

        return [permission() for permission in permission_classes]

    @action(methods=('POST', 'DELETE'),
            detail=True,
            url_path='subscribe',
            permission_classes=(IsAuthenticated,))
    def subscribtion(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            raise ValidationError(SELF_SUBSCRIBE_MESSAGE)
        if request.method == 'POST':
            subscribtion, created = Subscription.objects.get_or_create(
                user=user, author=author)
            if not created:
                raise ValidationError(SUBSCRIPTION_EXIST_MESSAGE)
            serializer = SubscriptionSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError(NO_SUBSCRIBTION_MESSAGE)
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',),
            detail=False,
            url_path='subscriptions',
            permission_classes=(IsAuthenticated,))
    def get_subscribtions(self, request):
        pages = self.paginate_queryset(
            User.objects.filter(subscriptions__user=request.user))
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
