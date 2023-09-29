from django.contrib.auth import get_user_model
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator
    )
from django.db import models
from django.http import HttpResponse
from django.db.models import Sum

User = get_user_model()


class Ingredient(models.Model):
    """Модель для ингредиентов в рецепте."""

    name = models.CharField(
        'Название ингредиента',
        max_length=100,
        blank=False,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=50,
        blank=False,
    )

    class Meta:
        ordering = ['id']
        verbose_name: str = 'ингредиент'
        verbose_name_plural: str = 'ингредиенты'
        unique_together = ('name', 'measurement_unit')

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    """Модель тэгов."""

    name = models.CharField(
        'Название тега',
        max_length=50,
        unique=True,
    )
    color = models.CharField(
        'HEX цвет тега',
        max_length=7,
        blank=False,
        unique=True,
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Поле должно содержать HEX-код выбранного цвета.'
            )
        ]
    )
    slug = models.SlugField(
        'Слаг',
        max_length=100,
        blank=False,
        unique=True,
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200,
        blank=False,
    )
    image = models.ImageField(
        'Изображение',
        upload_to='images_for_recipes/',
        blank=False,
    )
    text = models.TextField(
        verbose_name='Описание',
        blank=False,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='tags',
        db_index=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        blank=False,
        validators=[
            MaxValueValidator(600),
            MinValueValidator(1),
        ],
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self) -> str:
        return self.name

    def get_detail_recipe(self, user):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__userscarts__user=user,
            )
            .order_by('ingredient__name')
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(ingredient_value=Sum('amount'))
        )
        list_ingredients = ''
        list_ingredients += '\n'.join(
            [
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['ingredient_value']}"
                for ingredient in ingredients
            ],
        )
        return list_ingredients

class RecipeIngredient(models.Model):
    """Модель для количества ингредиентов в рецептах."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
        db_index=True,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиенты в рецепте',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество ингредиента',
        validators=[
            MinValueValidator(
                1,
                message='Указано количество ингредиента меньше 1',
            ),
            MaxValueValidator(
                50,
                message='Указано количество ингредиента больше 50')
        ],
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            ),
        ]

    def __str__(self) -> str:
        return self.ingredient.name


class Favorite(models.Model):
    """Модель рецептов в избранном."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            ),
        ]
        default_related_name = 'favorites'

    def __str__(self) -> str:
        user = self.user.username
        recipe = self.recipe.name
        return f'{user} добавил {recipe} в избранное.'


class UsersCart(models.Model):
    """Модель рецептов в списке покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'cписок покупок'
        verbose_name_plural = 'cписок покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_users_cart',
            ),
        ]
        default_related_name = 'userscarts'

    def __str__(self) -> str:
        user = self.user.username
        recipe = self.recipe.name
        return f'{user} добавил {recipe} в список покупок.'
