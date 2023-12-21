from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet,
    IngredientViewSet,
    TagViewSet,
    RecipeViewSet,
)


router = routers.DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
