from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

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


NO_IMAGE_MESSAGE = {'image': 'Это поле не может быть пустым.'}
NO_TAGS_MESSAGE = {'tags': 'Нужно выбрать хотя бы один тег!'}
SAME_TAGS_MESSAGE = 'Следующие теги не уникальны: {tags}'
NO_INGREDIENTS_MESSAGE = {
    'ingredients': 'Нужно выбрать хотя бы один ингердиент!'}
WRONG_INGREDIENT_MESSAGE = ('Следующие ингредиенты отсутствуют '
                            'в базе данных: {ingredient} ')
SAME_INGREDIENTS_MESSAGE = 'Следующие ингредиенты не уникальны: {ingredients}'
WRONG_AMOUNT_MESSAGE = {
    'amount': 'Количество ингредиента должно быть больше нуля!'}


class UserSerializer(DjoserUserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta():
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'is_subscribed')

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user,
            author=author
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
    id = serializers.PrimaryKeyRelatedField(
        read_only=True, source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        read_only=True, validators=(MinValueValidator(1),))

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_id(self, id):
        if not Ingredient.objects.filter(id=id).exists():
            raise serializers.ValidationError(
                WRONG_INGREDIENT_MESSAGE.format(ingredient=id)
            )
        return id


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

    def not_unique_items(self, items):
        return set([item for item in items if items.count(item) > 1])

    def validate(self, data):
        if not data.get('image'):
            raise serializers.ValidationError(NO_IMAGE_MESSAGE)
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(NO_TAGS_MESSAGE)
        if self.not_unique_items(tags):
            raise serializers.ValidationError(
                SAME_TAGS_MESSAGE.format(tags=self.not_unique_items(tags)))
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(NO_INGREDIENTS_MESSAGE)
        ingredients_out_of_database = [
            ingredient for ingredient in ingredients if not Ingredient.objects
            .filter(id=ingredient['id']).exists()
        ]
        if ingredients_out_of_database:
            raise serializers.ValidationError(
                WRONG_INGREDIENT_MESSAGE.format(
                    ingredient=ingredients_out_of_database
                ))
        if self.not_unique_items(
                [ingredient['id'] for ingredient in ingredients]):
            raise serializers.ValidationError(SAME_INGREDIENTS_MESSAGE.format(
                ingredients=self.not_unique_items(
                    [ingredient['id'] for ingredient in ingredients])
            ))
        return data

    def create_ingredients_amounts(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            ingredient=get_object_or_404(
                Ingredient, id=ingredient.get("id")),
            recipe=recipe,
            amount=ingredient.get("amount")
        ) for ingredient in ingredients])

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
        return RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientAmountSerializer(
        many=True, source='recipe')
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

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

    class Meta():
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = tuple(UserSerializer.Meta.fields) + \
            ('recipes', 'recipes_count')
        read_only_fields = ("email", "username", "first_name", "last_name")

    def get_recipes(self, obj):
        limit = self.context.get("request").GET.get("recipes_limit")
        recipes = obj.author.recipe.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            author=obj.author, user=self.context.get('request').user
        ).exists()
