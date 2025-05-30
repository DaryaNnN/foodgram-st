from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.response import Response

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
    filter_backends = [DjangoFilterBackend]   # добавляем фильтр
    filterset_fields = ['author']              # фильтрация по полю author (id пользователя)

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
