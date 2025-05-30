import json
import logging
import os

from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Ingredient

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def load_ingredients(sender, **kwargs):
    json_path = os.path.join(settings.BASE_DIR, "data", "ingredients.json")

    if not os.path.exists(json_path):
        logger.error(f"Файл {json_path} не найден")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {json_path}: {e}")
        return

    added_count = 0
    for item in data:
        obj, created = Ingredient.objects.get_or_create(
            name=item["name"], measurement_unit=item["measurement_unit"]
        )
        if created:
            logger.info(f"Добавлен ингредиент: {obj}")
            added_count += 1

    logger.info(f"Загрузка ингредиентов завершена, добавлено новых: {added_count}")
