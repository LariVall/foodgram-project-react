from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from api.filters import RecipeFilter
from api.paginations import PageAndLimitPagination
from api.permissions import AuthorOrAdminOrReadOnly
from api.serializers import (
    GetUserSerializer,
    IngredientSerializer,
    PostRecipeSerializer,
    RecipePreviewSerializer,
    RecipeSerializer,
    SubscriptionsSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
    UsersCart,
)
from users.models import UserSubscription

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)  # !!!!
    search_fields = ('^name',)  # !!!!


class GetUserViewSet(DjoserViewSet):

    pagination_class = PageAndLimitPagination  # !!!
    serializer_class = GetUserSerializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request) -> Response:
        queryset = User.objects.filter(followee__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request: Request, id: int) -> Response:
        user = self.request.user
        followee = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            if user != followee:
                if not UserSubscription.objects.filter(
                    user=user,
                    author=followee,
                ).exists():
                    UserSubscription.objects.create(
                        user=user,
                        author=followee,
                    )
                    serializer = SubscriptionsSerializer(
                        followee,
                        context={'request': request},
                    )
                    return Response(
                        data=serializer.data,
                        status=status.HTTP_201_CREATED,
                    )
        else:
            if UserSubscription.objects.filter(
                user=user,
                author=followee,
            ).exists():
                subscribe = get_object_or_404(
                    UserSubscription,
                    user=user,
                    author=followee,
                )
                subscribe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrAdminOrReadOnly,)  # !!!
    pagination_class = PageAndLimitPagination  # !!!
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = RecipeFilter  # !!!
    ordering = ('-id',)

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return PostRecipeSerializer
        elif self.request.method == 'GET':
            return RecipeSerializer

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
        serializer_class=RecipePreviewSerializer,
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk) -> Response:
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if not UsersCart.objects.filter(
                user=user,
                recipe=recipe,
            ).exists():
                UsersCart.objects.create(user=user, recipe=recipe)
                serializer = RecipePreviewSerializer(
                    recipe,
                    context={'request': request},
                )
                return Response(
                    data=serializer.data,
                    status=status.HTTP_201_CREATED,
                )
        else:
            users_cart = get_object_or_404(
                UsersCart,
                user=user,
                recipe=recipe,
            )
            users_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('post', 'delete'),
        detail=True,
        serializer_class=RecipePreviewSerializer(),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk) -> Response:
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if not Favorite.objects.filter(user=user, recipe=recipe).exists():
                Favorite.objects.create(user=user, recipe=recipe)
                serializer = RecipePreviewSerializer(
                    recipe,
                    context={'request': request},
                )
                return Response(
                    data=serializer.data,
                    status=status.HTTP_201_CREATED,
                )
        else:
            favorite = get_object_or_404(
                Favorite,
                user=user,
                recipe=recipe,
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request) -> HttpResponse:
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__userscarts__user=request.user,
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
        name = 'shopping_list.txt'
        response = HttpResponse(list_ingredients, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={name}'
        return response
