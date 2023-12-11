from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.db.models import F
from rest_framework.relations import SlugRelatedField
from rest_framework.fields import SerializerMethodField
from drf_extra_fields.fields import Base64ImageField

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


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta():
        model = User
        fields = tuple(UserSerializer.Meta.fields) + ('is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user,
            author=obj
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientWriteSerializer(
        many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        if not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Это поле не может быть пустым.'})
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужно выбрать хотя бы один тег!'})
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({'tags': 'Теги не уникальны!'})
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужно выбрать хотя бы один ингердиент!'})
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиент с id {ingredient} отсутствует в базе данных!'.format(ingredient=ingredient['id'])})
        items = [item['id'] for item in ingredients]
        if len(items) != len(set(items)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не уникальны!'})
        return data

    def create_ingredients_amounts(self, recipe, ingredients):
        ingredients_amounts = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, id=ingredient.get("id")
            )
            ingredients_amounts.append(RecipeIngredient(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient.get("amount")
            ))
        RecipeIngredient.objects.bulk_create(ingredients_amounts)

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients_amounts(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        self.create_ingredients_amounts(recipe, ingredients)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = IngredientAmountSerializer(
        many=True, source='recipe')
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return ShoppingList.objects.filter(recipe=obj, user=user).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='recipe.name')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    image = Base64ImageField(source='recipe.image')

    class Meta():
        model = ShoppingList
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(CustomUserSerializer):
    recipes = ShortRecipeSerializer(many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = tuple(CustomUserSerializer.Meta.fields) + \
            ('recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()
