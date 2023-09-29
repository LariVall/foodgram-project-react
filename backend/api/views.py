from django.contrib.auth import get_user_model
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
    """Viewset для модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset для модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class GetUserViewSet(DjoserViewSet):
    """Viewset для работы с моделью User."""

    pagination_class = PageAndLimitPagination
    serializer_class = GetUserSerializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request) -> Response:
        """Метод для запроса к эндпоинту subscriptions."""
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
        """Метод для запроса к эндпоинту subscribe."""
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
    """Viewset для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrAdminOrReadOnly,)
    pagination_class = PageAndLimitPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = RecipeFilter
    ordering = ('-id',)

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return PostRecipeSerializer
        elif self.request.method == 'GET':
            return RecipeSerializer

    def _relations(request, instance, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if not instance.objects.filter(
                user=user,
                recipe=recipe,
            ).exists():
                instance.objects.create(user=user, recipe=recipe)
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
                instance,
                user=user,
                recipe=recipe,
            )
            users_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
        serializer_class=RecipePreviewSerializer,
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk) -> Response:
        """Метод для запроса к эндпоинту shopping_cart."""
        return self._relations(request, UsersCart, pk)

    @action(
        methods=('post', 'delete'),
        detail=True,
        serializer_class=RecipePreviewSerializer(),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk) -> Response:
        """Метод для запроса к эндпоинту favorite."""
        return self._relations(request, Favorite, pk)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request) -> HttpResponse:
        """Метод для запроса к эндпоинту download_shopping_cart."""
        list_ingredients = Recipe.get_detail_recipe(request.user)
        name = 'shopping_list.txt'
        response = HttpResponse(list_ingredients, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={name}'
        return response
