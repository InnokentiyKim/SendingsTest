from django.db import models


class Sending(models.Model):
    """Model for tracking email sending tasks."""

    external_id = models.CharField(
        "Внешний идентификатор",
        max_length=255,
        unique=True,
        db_index=True,
    )
    user_id = models.CharField("ID пользователя", max_length=255)
    email = models.EmailField("Email получателя")
    subject = models.CharField("Тема письма", max_length=255)
    message = models.TextField("Текст письма")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Sending {self.external_id} → {self.email}"
