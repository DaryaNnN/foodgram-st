import json
import logging
import os

from django.conf import settings
from django.core.files import File
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Ingredient, Recipe, RecipeIngredient

logger = logging.getLogger(__name__)
User = get_user_model()


def load_json(filename):
    path = os.path.join(settings.BASE_DIR, "data", filename)
    if not os.path.exists(path):
        logger.error(f"Файл {filename} не найден по пути {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@receiver(post_migrate)
def load_test_data(sender, **kwargs):
    # Загружаем пользователей
    users_data = load_json("users.json")
    for user_data in users_data:
        user, created = User.objects.get_or_create(email=user_data["email"], defaults={
            "username": user_data["username"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
        })
        if created:
            user.set_password(user_data["password"])
            avatar_path = os.path.join(settings.MEDIA_ROOT, user_data["avatar"])
            if os.path.exists(avatar_path):
                with open(avatar_path, "rb") as avatar_file:
                    user.avatar.save(os.path.basename(avatar_path), File(avatar_file), save=False)
            user.save()
            logger.info(f"Создан пользователь: {user.email} с аватаркой")
        else:
            logger.info(f"Пользователь {user.email} уже существует")

    # Загружаем ингредиенты (уже есть у тебя, можно оставить)
    ingredients_data = load_json("ingredients.json")
    for item in ingredients_data:
        obj, created = Ingredient.objects.get_or_create(
            name=item["name"], measurement_unit=item["measurement_unit"]
        )
        if created:
            logger.info(f"Добавлен ингредиент: {obj}")

    # Загружаем рецепты
    recipes_data = load_json("recipes.json")
    for recipe_data in recipes_data:
        try:
            author = User.objects.get(email=recipe_data["author_email"])
        except User.DoesNotExist:
            logger.error(f"Автор с email {recipe_data['author_email']} не найден, рецепт пропущен")
            continue

        recipe, created = Recipe.objects.get_or_create(
            author=author,
            name=recipe_data["name"],
            defaults={
                "text": recipe_data["text"],
                "cooking_time": recipe_data["cooking_time"],
            },
        )
        if created:
            # Загружаем изображение рецепта
            image_path = os.path.join(settings.MEDIA_ROOT, recipe_data["image"])
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    recipe.image.save(os.path.basename(image_path), File(image_file), save=False)

            recipe.save()
            logger.info(f"Добавлен рецепт: {recipe.name}")

            # Добавляем ингредиенты к рецепту с количеством
            for ingredient_data in recipe_data["ingredients"]:
                ingredient, _ = Ingredient.objects.get_or_create(
                    name=ingredient_data["name"],
                    measurement_unit=ingredient_data["measurement_unit"],
                )
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ingredient,
                    defaults={"amount": ingredient_data["amount"]}
                )
        else:
            logger.info(f"Рецепт {recipe.name} уже существует")
