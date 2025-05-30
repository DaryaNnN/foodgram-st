from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from recipes.models import Ingredient
from recipes.serializers import IngredientSerializer


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
