from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.paginations import PageAndLimitPagination
from api.permissions import AuthorOrAdminOrReadOnly
from api.serializers import (
    GetUserSerializer,
    IngredientSerializer,
    PostRecipeSerializer,
    RecipeSerializer,
    SubscriptionsSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    Tag,
    UsersCart,
)
from users.models import UserSubscription

from .mixins import AddDeleteMixin

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


class RecipeViewSet(viewsets.ModelViewSet, AddDeleteMixin):
    """Viewset для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrAdminOrReadOnly,)
    pagination_class = PageAndLimitPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = RecipeFilter
    ordering = ('-id',)

    # def perform_create(self, serializer: Serializer) -> None:
    #     serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return PostRecipeSerializer

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

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, pk)
        return self.delete_from(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_to(UsersCart, request.user, pk)
        return self.delete_from(UsersCart, request.user, pk)
