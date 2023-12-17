from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator


LENGTH_LIMITS_USER_FIELDS = 150
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
    email = models.EmailField(
        blank=False,
        unique=True
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
        blank=False
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
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return INGREDIENT.format(
            name=self.name,
            measurement_unit=self.measurement_unit
        )


class Recipe(models.Model):
    """Модель рецептов."""

    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        blank=False,
        verbose_name='Тэги'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        blank=False,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipe',
        blank=False,
        verbose_name='Ингредиенты'
    )
    name = models.CharField(
        'Название',
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS,
        blank=False
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=False,
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
        auto_now_add=True,
        db_index=True
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


class RecipeTag(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=False,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        blank=False,
        verbose_name='Тэг'
    )

    class Meta:
        verbose_name = 'Рецепт/тег'
        verbose_name_plural = 'Рецепты/теги'
        constraints = [models.UniqueConstraint(
            fields=['tag', 'recipe'],
            name='unique_recipe_tag'
        )]

    def __str__(self):
        return f'{self.recipe} / {self.tag}'


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe',
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
        'Количество',
        validators=(MinValueValidator(1),)
    )

    class Meta:
        verbose_name = 'Рецепт/ингредиент'
        verbose_name_plural = 'Рецепты/ингредиенты'
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
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bloger',
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
