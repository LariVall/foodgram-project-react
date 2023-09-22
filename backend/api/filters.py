from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import (
    BooleanFilter,
    ModelMultipleChoiceFilter,
)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтрация рецептов по включению их в избранном пользователя и списке
    покупок пользователя.
    """

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model: Recipe = Recipe
        fields = ['tags', 'author']

    def filter_is_favorited(
        self, queryset, name, value,
    ):
        """Фильтрация по наличию рецептов в избранном пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        else:
            return queryset

    def filter_is_in_shopping_cart(
        self, queryset, name, value,
    ):
        """Фильтрация по наличию рецептов в списке покупок пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(userscarts__user=self.request.user)
        else:
            return queryset
