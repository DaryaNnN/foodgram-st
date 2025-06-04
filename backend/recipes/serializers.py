from rest_framework import serializers, generics, permissions

from foodgram.constants import (
    MIN_INGREDIENT_AMOUNT,
    MAX_INGREDIENT_AMOUNT,
    MAX_COOKING_TIME,
    MIN_COOKING_TIME,
)
from users.serializers import Base64ImageField, UserSerializer
from .models import Recipe, Ingredient, RecipeIngredient


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="component"
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT, max_value=MAX_INGREDIENT_AMOUNT
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="component.id")
    name = serializers.CharField(source="component.name")
    measurement_unit = serializers.CharField(source="component.measurement_unit")
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


def create_recipe_ingredients(recipe, ingredients_data):
    RecipeIngredient.objects.bulk_create(
        [
            RecipeIngredient(
                recipe=recipe,
                component=ingredient["component"],
                amount=ingredient["amount"],
            )
            for ingredient in ingredients_data
        ]
    )


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True, write_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = ("id", "name", "text", "cooking_time", "image", "ingredients")

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Нужно указать хотя бы один ингредиент.")

        ingredient_ids = set()
        for ingredient in value:
            component = ingredient["component"]
            if component in ingredient_ids:
                raise serializers.ValidationError("Ингредиенты не должны повторяться.")
            ingredient_ids.add(component)
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        user = self.context["request"].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            create_recipe_ingredients(instance, ingredients_data)

        return instance

    def validate(self, data):
        if self.instance and not self.partial and "ingredients" not in data:
            raise serializers.ValidationError({"ingredients": "Это поле обязательно."})
        if self.partial and "ingredients" not in data:
            raise serializers.ValidationError(
                {"ingredients": "Это поле обязательно при обновлении."}
            )
        return data


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    image = serializers.ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        ]

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.in_carts.filter(user=user).exists()


class RecipeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return RecipeCreateSerializer
        return RecipeListSerializer


class RecipeCartSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            return request.build_absolute_uri(obj.image.url)
        return None


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
