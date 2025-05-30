from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Ingredient, Recipe
from recipes.serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
)


class IngredientListView(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]
    pagination_class = None


class IngredientDetailView(generics.RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]


class RecipeListCreateView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]  # добавляем фильтр
    filterset_fields = ['author']  # фильтрация по полю author (id пользователя)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecipeCreateSerializer
        return RecipeListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        output_serializer = RecipeListSerializer(recipe, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class RecipeDetailView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeListSerializer
    permission_classes = [permissions.AllowAny]  # публичный доступ


class RecipeGetLinkView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)

        # Получаем полный URL текущего рецепта
        full_url = request.build_absolute_uri(f'/api/recipes/{recipe.id}/')

        return Response({"short-link": full_url}, status=status.HTTP_200_OK)
