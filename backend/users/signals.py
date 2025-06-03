import json
import logging
import os

from django.conf import settings
from django.core.files import File
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

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
def load_test_users(sender, **kwargs):
    users_data = load_json("users.json")
    if not users_data:
        return

    emails = [u["email"] for u in users_data]
    existing_users = {u.email: u for u in User.objects.filter(email__in=emails)}

    for user_data in users_data:
        email = user_data["email"]
        if email in existing_users:
            logger.info(f"Пользователь {email} уже существует")
            continue

        user = User(
            email=email,
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
        )
        user.set_password(user_data["password"])

        avatar_path = os.path.join(settings.MEDIA_ROOT, user_data["avatar"])
        if os.path.exists(avatar_path):
            with open(avatar_path, "rb") as avatar_file:
                user.avatar.save(
                    os.path.basename(avatar_path), File(avatar_file), save=False
                )

        user.save()
        logger.info(f"Создан пользователь: {email} с аватаркой")
