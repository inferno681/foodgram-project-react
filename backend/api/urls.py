from django.urls import include, path
from rest_framework import routers

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    TagViewSet,
    RecipeViewSet,
)


router_v1 = routers.DefaultRouter()
router_v1.register(r'tags', TagViewSet, basename='tag')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredient')
router_v1.register(r'recipes', RecipeViewSet, basename='recipe')
router_v1.register(r'users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
