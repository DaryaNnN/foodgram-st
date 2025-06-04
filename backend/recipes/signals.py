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


def create_ingredients(ingredients_data):
    existing_ingredients = {
        (i.name.lower(), i.measurement_unit.lower()) for i in Ingredient.objects.all()
    }
    new_ingredients = []
    for item in ingredients_data:
        key = (item["name"].lower(), item["measurement_unit"].lower())
        if key not in existing_ingredients:
            new_ingredients.append(
                Ingredient(name=item["name"], measurement_unit=item["measurement_unit"])
            )
    Ingredient.objects.bulk_create(new_ingredients)
    logger.info(f"Добавлено ингредиентов: {len(new_ingredients)}")


def create_recipes(recipes_data):
    author_emails = {r["author_email"] for r in recipes_data}
    authors = {u.email: u for u in User.objects.filter(email__in=author_emails)}

    all_ingredients = Ingredient.objects.all()
    ingredient_lookup = {
        (i.name.lower(), i.measurement_unit.lower()): i for i in all_ingredients
    }

    for recipe_data in recipes_data:
        author = authors.get(recipe_data["author_email"])
        if not author:
            logger.error(
                f"Автор с email {recipe_data['author_email']} не найден, рецепт пропущен"
            )
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
            image_path = os.path.join(settings.MEDIA_ROOT, recipe_data["image"])
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    recipe.image.save(
                        os.path.basename(image_path), File(image_file), save=False
                    )
            recipe.save()
            logger.info(f"Добавлен рецепт: {recipe.name}")

            new_links = []
            for ingredient_data in recipe_data["ingredients"]:
                key = (
                    ingredient_data["name"].lower(),
                    ingredient_data["measurement_unit"].lower(),
                )
                ingredient = ingredient_lookup.get(key)
                if not ingredient:
                    logger.warning(
                        f"Ингредиент {key} не найден для рецепта {recipe.name}"
                    )
                    continue

                new_links.append(
                    RecipeIngredient(
                        recipe=recipe,
                        component=ingredient,
                        amount=ingredient_data["amount"],
                    )
                )

            RecipeIngredient.objects.bulk_create(new_links)
        else:
            logger.info(f"Рецепт {recipe.name} уже существует")


@receiver(post_migrate)
def load_test_data(sender, **kwargs):
    ingredients_data = load_json("ingredients.json")
    if ingredients_data:
        create_ingredients(ingredients_data)

    recipes_data = load_json("recipes.json")
    if recipes_data:
        create_recipes(recipes_data)
