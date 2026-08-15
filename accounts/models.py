from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

USERNAME_REGEX_VALIDATOR = RegexValidator(
    regex=r"^[a-zA-Z0-9_]{3,20}$",
    message="Kullanıcı adı 3-20 karakter olmalı, sadece harf, rakam ve alt çizgi içerebilir.",
)

FORBIDDEN_USERNAMES = {
    "admin", "root", "api", "static", "anket", "giris",
    "kayit", "cikis", "kullanici", "hakkinda",
}


def validate_username_not_forbidden(value):
    if value.lower() in FORBIDDEN_USERNAMES:
        raise ValidationError("Bu kullanıcı adı kullanılamaz.")


class User(AbstractUser):
    username = models.CharField(
        max_length=20,
        unique=True,
        validators=[USERNAME_REGEX_VALIDATOR, validate_username_not_forbidden],
    )
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)
