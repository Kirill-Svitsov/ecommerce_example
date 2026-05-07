from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from catalog.models import Item


class Favourite(models.Model):
    """Избранное пользователя."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favourites", verbose_name=_("пользователь")
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="favourited_by", verbose_name=_("товар")
    )
    position = models.PositiveIntegerField(_("позиция"), default=0)
    on_moodboard = models.BooleanField(_("в мудборде"), default=True)
    moodboard_position = models.PositiveIntegerField(_("позиция в мудборде"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("избранное")
        verbose_name_plural = _("избранное")
        ordering = ["position"]
        unique_together = ["user", "item"]
        indexes = [
            models.Index(fields=["user", "on_moodboard"]),
            models.Index(fields=["user", "position"]),
            models.Index(fields=["user", "moodboard_position"]),
        ]

    def __str__(self):
        mood = " (M)" if self.on_moodboard else ""
        return f"{self.user.email} - {self.item.name_ru} pos:{self.position}{mood}"
