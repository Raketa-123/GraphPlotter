from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField("почта", unique=True)

class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="questions")
    title = models.CharField("Название/Функция", max_length=255)
    graph_image = models.ImageField("График", upload_to="graphs/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Запрос графика"
        verbose_name_plural = "Запросы графиков"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} -> {self.title}"