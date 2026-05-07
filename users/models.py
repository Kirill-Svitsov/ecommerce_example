from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("User with this email already exists."),
        },
    )
    phone = models.CharField(
        _("phone number"),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Optional. Format: +7XXXXXXXXXX"),
    )
    is_subscribed = models.BooleanField(
        _("subscribed to newsletter"),
        default=True,
        help_text=_("Designates whether the user receives marketing emails."),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = "users_user"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_subscribed"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
