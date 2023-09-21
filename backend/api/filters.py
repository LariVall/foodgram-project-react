from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import (
    BooleanFilter,
    ModelMultipleChoiceFilter,
)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):

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
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(favorites__user=self.request.user)
        else:
            return queryset

    def filter_is_in_shopping_cart(
        self, queryset, name, value,
    ):
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(userscarts__user=self.request.user)
        else:
            return queryset
