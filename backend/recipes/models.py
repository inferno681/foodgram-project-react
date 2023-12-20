from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator

from .validators import validate_color, validate_username


LENGTH_LIMITS_USER_FIELDS = 150
LENGTH_LIMITS_EMAIL_FIELD = 200
LENGTH_LIMITS_NAME_AND_SLUG_FIELDS = 200
TAG = (
    'Название: {name:.15}. '
    'Цвет: {color:.7}. '
    'Слаг: {slug:.15}. '
)
INGREDIENT = (
    'Название: {name:.15}. '
    'Единица измерения: {measurement_unit:.15}. '
)
RECIPE = (
    'Название: {name:.15}. '
    'Текст: {text:.15}. '
    'Дата публикации: {pub_date}. '
)
SELF_SUBSCRIBE_MESSAGE = 'Нельзя подписаться на себя!'


class User(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    username = models.CharField(
        db_index=True,
        max_length=LENGTH_LIMITS_USER_FIELDS,
        unique=True,
        validators=(validate_username,)
    )
    email = models.EmailField(
        blank=False,
        unique=True,
        max_length=LENGTH_LIMITS_EMAIL_FIELD,
    )
    first_name = models.CharField(
        'Имя',
        max_length=LENGTH_LIMITS_USER_FIELDS,
        blank=False
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LENGTH_LIMITS_USER_FIELDS,
        blank=False
    )
    password = models.CharField(
        max_length=LENGTH_LIMITS_USER_FIELDS,
        blank=False
    )

    def __str__(self):
        return self.username

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(
        'Название',
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS,
        unique=True,
        blank=False
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True,
        blank=False,
        validators=(validate_color,)
    )
    slug = models.SlugField(
        'Слаг',
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS,
        unique=True,
        blank=False
    )

    class Meta:
        ordering = ('slug',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return TAG.format(
            name=self.name,
            color=self.color,
            slug=self.slug
        )


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        'Название',
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS,
        blank=False
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS,
        blank=False
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return INGREDIENT.format(
            name=self.name,
            measurement_unit=self.measurement_unit
        )


class Recipe(models.Model):
    """Модель рецептов."""

    tags = models.ManyToManyField(
        Tag,
        blank=False,
        verbose_name='Тэги'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        blank=False,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        blank=False,
        verbose_name='Продукты'
    )
    name = models.CharField(
        'Название',
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS,
        blank=False
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=False,
        default=None,
        blank=False
    )
    text = models.TextField(
        'Текст',
        blank=False
    )
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=(MinValueValidator(1),),
        blank=False
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return RECIPE.format(
            name=self.name,
            text=self.text,
            pub_date=self.pub_date,
        )


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipes',
        on_delete=models.CASCADE,
        blank=False,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        blank=False,
        verbose_name='Ингредиент'

    )
    amount = models.IntegerField(
        'Мера',
        validators=(MinValueValidator(1),)
    )

    class Meta:
        verbose_name = 'Рецепт-ингредиент'
        verbose_name_plural = 'Рецепты-ингредиенты'
        constraints = [models.UniqueConstraint(
            fields=['ingredient', 'recipe'],
            name='unique_recipe_ingredient'
        )]

    def __str__(self):
        return f'{self.recipe} / {self.ingredient} / {self.amount}'


class UserRecipeAbstractModel(models.Model):
    """Абстрактная модель для избранного и списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        related_name='%(class)ss',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
        related_name='%(class)ss',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_user_recipe(%(class)s)'
        )]

    def __str__(self):
        return str(self.user) + '/' + str(self.recipe)


class Favorite(UserRecipeAbstractModel):
    """Модель избранного."""

    class Meta(UserRecipeAbstractModel.Meta):

        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранное'


class ShoppingList(UserRecipeAbstractModel):
    """Модель списка покупок."""
    class Meta(UserRecipeAbstractModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Subscription(models.Model):
    """Модель подписчиков."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_as_user',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Блогер'
    )

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'],
            name='unique_subscription'
        )]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def clean(self):
        super().clean()
        if self.user == self.author:
            raise ValidationError(SELF_SUBSCRIBE_MESSAGE)

    def __str__(self):
        return str(self.user) + '/' + str(self.author)
