from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from recipes.models import Ingredient, Recipe, ShoppingList, RecipeIngredient, Favorite
from recipes.serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer, RecipeCartSerializer, RecipeShortSerializer,
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

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

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

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        params = self.request.query_params

        if user.is_authenticated:
            if params.get("is_favorited") in ["1", "true", "True"]:
                queryset = queryset.filter(favorites__user=user)

            if params.get("is_in_shopping_cart") in ["1", "true", "True"]:
                queryset = queryset.filter(in_carts__user=user)

        if "author" in params:
            queryset = queryset.filter(author__id=params["author"])

        return queryset

class RecipeGetLinkView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)

        # Получаем полный URL текущего рецепта
        full_url = request.build_absolute_uri(f'/api/recipes/{recipe.id}/')

        return Response({"short-link": full_url}, status=status.HTTP_200_OK)

class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeListSerializer

    def patch(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        read_serializer = RecipeListSerializer(instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)

class ShoppingCartAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"detail": "Рецепт уже в корзине."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ShoppingList.objects.create(user=user, recipe=recipe)

        serializer = RecipeCartSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        cart_item = ShoppingList.objects.filter(user=user, recipe=recipe).first()
        if not cart_item:
            return Response(
                {"detail": "Рецепт не найден в корзине."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DownloadShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        shopping_items = ShoppingList.objects.filter(user=user)

        if not shopping_items.exists():
            return Response({"detail": "Корзина пуста."}, status=400)

        # Собираем ингредиенты со всеми рецептами в корзине
        ingredients = {}

        for item in shopping_items:
            recipe = item.recipe
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            for ri in recipe_ingredients:
                name = ri.component.name
                unit = ri.component.measurement_unit
                amount = ri.amount
                if name in ingredients:
                    ingredients[name]['amount'] += amount
                else:
                    ingredients[name] = {'amount': amount, 'unit': unit}

        # Формируем текстовый файл со списком покупок
        lines = []
        for name, data in ingredients.items():
            lines.append(f"{name} — {data['amount']} {data['unit']}")

        content = "\n".join(lines)

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

class FavoriteAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"detail": "Рецепт уже в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Favorite.objects.create(user=user, recipe=recipe)

        serializer = RecipeShortSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            return Response(
                {"detail": "Рецепт не найден в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
