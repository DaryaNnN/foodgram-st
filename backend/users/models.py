from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        "Email",
        max_length=254,
        unique=True,
    )
    first_name = models.CharField("Имя", blank=False, max_length=150)
    last_name = models.CharField("Фамилия", blank=False, max_length=150)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["id"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",  # Я подписан на
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribers",  # Кто подписан на меня
        verbose_name="Автор",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"],
                name="unique_subscription",
            )
        ]

    def __str__(self) -> str:
        return f"{self.subscriber} подписан на {self.author}"
