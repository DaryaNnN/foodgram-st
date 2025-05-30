from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from recipes.models import Ingredient, Recipe
from recipes.serializers import IngredientSerializer, RecipeCreateSerializer, RecipeListSerializer


class IngredientListView(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]  # фильтруем по name
    pagination_class = None


class IngredientDetailView(generics.RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]



from rest_framework.response import Response
from rest_framework import status

class RecipeListCreateView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecipeCreateSerializer
        return RecipeListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        # Сериализуем созданный рецепт полным сериализатором (для корректного ответа)
        output_serializer = RecipeListSerializer(recipe, context={'request': request})

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
