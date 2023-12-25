from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    SAFE_METHODS
)
from rest_framework.response import Response

from .filters import RecipeFilter
from .functions import get_shopping_list_text
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
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
SHOPPING_LIST_FILE_NAME = '{date}_{username}_shopping_list.txt'
RECIPE_IN_FAVORITES_MESSAGE = {'errors': 'Рецепт уже в избранном!'}
NO_RECIPE_IN_FAVORITE_MESSAGE = {'errors': 'Рецепта нет в избранном!'}
SELF_SUBSCRIBE_MESSAGE = {'errors': 'Нельзя подписаться на себя!'}
SUBSCRIPTION_EXIST_MESSAGE = {'errors': 'Вы уже подписаны на этого автора!'}
NO_SUBSCRIBTION_MESSAGE = {'errors': 'Нельзя удалить несуществующую подписку!'}


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
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

    @staticmethod
    def add_delete_obj(request, pk, model, message):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                raise ValidationError(message)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(model, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=('POST', 'DELETE'),
            detail=True,
            url_path='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return RecipeViewSet.add_delete_obj(
            request,
            pk,
            ShoppingList,
            RECIPE_IN_SHOPPING_LIST_MESSAGE
        )

    @action(methods=('GET',),
            detail=False,
            url_path='download_shopping_cart',
            permission_classes=(IsAuthenticated,))
    def download_shopping_list(self, request):
        user = request.user
        if not ShoppingList.objects.filter(user=user).exists():
            raise ValidationError(SHOPPING_LIST_EMPTY_MESSAGE)
        filename = SHOPPING_LIST_FILE_NAME.format(
            date=timezone.now().strftime("%d-%m-%Y"),
            username=user.username
        )
        return FileResponse(
            get_shopping_list_text(user),
            content_type='text/plain',
            filename=filename
        )

    @action(methods=('POST', 'DELETE'),
            detail=True,
            url_path='favorite',
            permission_classes=(IsAuthenticated,))
    def favorites(self, request, pk):
        return RecipeViewSet.add_delete_obj(
            request,
            pk,
            Favorite,
            RECIPE_IN_FAVORITES_MESSAGE
        )


class UserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.request.path == '/api/users/me/':
            return (IsAuthenticated(),)
        return super().get_permissions()

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
            _, created = Subscription.objects.get_or_create(
                user=user, author=author)
            if not created:
                raise ValidationError(SUBSCRIPTION_EXIST_MESSAGE)
            serializer = SubscriptionSerializer(
                author, context=self.get_serializer_context())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscribtion = get_object_or_404(
            Subscription, user=user, author=author)
        subscribtion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',),
            detail=False,
            url_path='subscriptions',
            permission_classes=(IsAuthenticated,))
    def get_subscribtions(self, request):
        pages = self.paginate_queryset(
            User.objects.filter(subscriptions__user=request.user))
        serializer = SubscriptionSerializer(
            pages, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)
