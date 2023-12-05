from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator


LENGTH_LIMITS_USER_FIELDS = 150
LENGTH_LIMITS_NAME_AND_SLUG_FIELDS = 200
TAG = (
    'Название: {name:.15}. '
    'Цвет: {color:.7}. '
)


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        'Адрес электронной почты',
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
    name = models.CharField(max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS)
    color = models.CharField(max_length=7)
    slug = models.SlugField(
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS)
    measurement_unit = models.CharField(
        max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    tags = models.ManyToManyField(Tag, through='RecipeTag')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipe')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient')
    name = models.CharField(max_length=LENGTH_LIMITS_NAME_AND_SLUG_FIELDS)
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    text = models.TextField()
    cooking_time = models.IntegerField(validators=MinValueValidator(1))
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=False,
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        blank=False,
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
        on_delete=models.CASCADE,
        blank=False,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        blank=False,
    )
    amount = models.IntegerField(validators=MinValueValidator(1))

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
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
    )

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_user_recipe'
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


class Follow(models.Model):
    """Модель подписчиков."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['author', 'follower'],
            name='unique_following'
        )]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return str(self.author) + '/' + str(self.follower)
