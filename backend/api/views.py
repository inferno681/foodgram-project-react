from django.shortcuts import render
from rest_framework import mixins, viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse
from djoser.views import UserViewSet

from recipes.models import (
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
from .serializers import (IngredientSerializer,
                          TagSerializer,
                          RecipeSerializer,
                          RecipeWriteSerializer,
                          ShortRecipeSerializer,
                          SubscriptionSerializer)
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly


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
    filterset_fields = ['author', 'tags']
    permission_classes = (IsAuthorOrReadOnly,)

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
        if not Recipe.objects.filter(id=pk).exists():
            raise ValidationError(
                {'errors': 'Такого рецепта не существует!'})
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            shopping_list, created = ShoppingList.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                raise ValidationError(
                    {'errors': 'Рецепт уже в списке покупок!'})
            serializer = ShortRecipeSerializer(shopping_list)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        shopping_list = get_object_or_404(
            ShoppingList,
            user=user,
            recipe=recipe
        )
        shopping_list.delete()
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
        if not Recipe.objects.filter(id=pk).exists():
            raise ValidationError(
                {'errors': 'Такого рецепта не существует!'})
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                raise ValidationError(
                    {'errors': 'Рецепт уже в избранном!'})
            serializer = ShortRecipeSerializer(favorite)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = get_object_or_404(
            ShoppingList,
            user=user,
            recipe=recipe
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    @action(methods=('POST', 'DELETE'),
            detail=True,
            url_path='subscribe',
            permission_classes=(IsAuthenticated,))
    def subscribtion(self, request, id):
        user = request.user
        if not User.objects.filter(id=id).exists():
            raise ValidationError(
                {'errors': 'Такого автора не существует!'})
        author = get_object_or_404(User, id=id)
        if user == author:
            raise ValidationError(
                {'errors': 'нельзя подписаться на себя!'})
        if request.method == 'POST':
            subscribtion, created = Subscription.objects.get_or_create(
                user=user, author=author)
            if not created:
                raise ValidationError(
                    {'errors': 'Автор уже в избранном!'})
            serializer = SubscriptionSerializer(
                subscribtion)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        author = get_object_or_404(
            Subscription,
            user=user,
            author=author
        )
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',),
            detail=False,
            url_path='subscribtions',
            permission_classes=(IsAuthenticated,))
    def subscribtions(self, request):
        bloger = request.user.subscriber.all()
        pages = self.paginate_queryset(bloger)
        serializer = SubscriptionSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)
