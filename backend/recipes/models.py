from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):

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

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):

    name = models.CharField(
        'Название тега',
        max_length=50,
        blank=False,
        unique=True,
        db_index=True,
    )
    color = models.CharField(
        'HEX цвет тега',
        max_length=7,
        blank=False,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=100,
        blank=False,
        unique=True,
        db_index=True,
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
        db_index=True,
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
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        blank=False,
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


class RecipeIngredient(models.Model):

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
                message='Указано количество ингредиента меньше 1 минуты.',
            ),
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
