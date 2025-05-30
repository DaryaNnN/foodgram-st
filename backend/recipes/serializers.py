from rest_framework import serializers
from users.serializers import Base64ImageField, UserSerializer
from .models import Recipe, Ingredient, RecipeIngredient


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='component'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='component.id')
    name = serializers.CharField(source='component.name')
    measurement_unit = serializers.CharField(source='component.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True, write_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'cooking_time', 'image', 'ingredients')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Нужно указать хотя бы один ингредиент.')
        ingredient_ids = []
        for ingredient in value:
            ingredient_obj = ingredient['component'] if isinstance(ingredient['component'], Ingredient) else ingredient['component']
            if ingredient_obj in ingredient_ids:
                raise serializers.ValidationError('Ингредиенты не должны повторяться.')
            ingredient_ids.append(ingredient_obj)
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError('Количество ингредиента должно быть положительным.')
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user, **validated_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                component=ingredient_data['component'],
                amount=ingredient_data['amount']
            )
        return recipe


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    image = serializers.ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        ]

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.in_carts.filter(user=user).exists()
