import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import UserSubscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор для изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext: str = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов"""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class UserCreatorSerializer(DjoserUserCreateSerializer):
    """Сериализатор создания пользователя."""

    email = serializers.EmailField(
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Такой email уже существует в базе!',
            ),
        ],
    )
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Такой username уже существует в базе!',
            ),
            User.username_validator,
        ],
    )
    password = serializers.CharField(
        write_only=True,
    )
    first_name = serializers.CharField(
        max_length=150,
    )
    last_name = serializers.CharField(
        max_length=150,
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'password',
            'first_name',
            'last_name',
        )


class GetUserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj: User) -> bool:
        """Метод проверки подпиcки пользователя на автора."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return UserSubscription.objects.filter(
                user=user, author=obj,
            ).exists()
        elif user.is_anonymous:
            return False

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )


class RecipePreviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов в укороченном виде."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок на автора."""

    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(GetUserSerializer.Meta):
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'username',
            'is_subscribed',
            'recipes_count',
            'recipes',
        )

    def get_is_subscribed(self, obj) -> bool:
        """Метод проверки подписки на автора рецептов."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return UserSubscription.objects.filter(
                user=user, author=obj,
            ).exists()
        elif user.is_anonymous:
            return False

    def get_recipes_count(self, obj) -> int:
        """Метод получения количества рецептов у автора рецептов."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Метод получения всех рецептов автора."""
        request = self.context.get('request')
        limit = int(request.query_params.get('recipes_limit', '5'))
        recipes = obj.recipes.all()[:limit]
        return RecipePreviewSerializer(many=True).to_representation(
            recipes,
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id',
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True,
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True,
    )
    amount = serializers.IntegerField(
        min_value=1,
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор получения рецептов."""

    image = serializers.ReadOnlyField(source='image.url')
    author = GetUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
    )
    tags = TagSerializer(many=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'image',
            'author',
            'name',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'pub_date',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj) -> bool:
        """Метод для проверки наличия рецепта в избранном."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.favorites.filter(user=user).exists()
        elif user.is_anonymous:
            return False

    def get_is_in_shopping_cart(self, obj) -> bool:
        """Метод проверки рецепта в списке покупок."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.userscarts.filter(user=user).exists()
        elif user.is_anonymous:
            return False


class PostRecipeSerializer(RecipeSerializer):
    """Сериализатор для создания или изменения рецептов."""

    image = Base64ImageField()
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    cooking_time = serializers.IntegerField()

    @transaction.atomic
    def create(self, validated_data) -> Recipe:
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = super().create(validated_data)
        for item in ingredients:
            ingredient = item['ingredient']['id']
            recipe_ingredient = RecipeIngredient(
                ingredient=ingredient,
                recipe=recipe,
                amount=item['amount']
                )
            ingredients.append(recipe_ingredient)

        RecipeIngredient.objects.bulk_create(ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance: Recipe, validated_data) -> Recipe:
        """Метод обновления рецепта."""
        ingredients = validated_data.pop('recipe_ingredients', None)
        recipe = super().update(instance, validated_data)
        instance.ingredients.clear()
        for item in ingredients:
            ingredient_id = item['ingredient']['id']
            amount = item['amount']
            recipe_ingredient = RecipeIngredient(
                ingredient_id=ingredient_id,
                recipe=recipe,
                amount=amount
                )
            ingredients.append(recipe_ingredient)

        RecipeIngredient.objects.bulk_create(ingredients)
        return recipe

    def validate_ingredients(self, ingredients):
        """Метод валидации ингредиентов."""
        unique_ingredient = set()
        for item in ingredients:
            ingredient_id = item.get('ingredient', {}).get('id')
            if ingredient_id:
                unique_ingredient.add(ingredient_id)
        if len(unique_ingredient) != len(ingredients):
            raise ValidationError('Ингредиенты должны быть уникальными')
        return ingredients
