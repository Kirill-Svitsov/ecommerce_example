from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class Contact(models.Model):
    """Контактные данные магазина (только одна запись)"""

    phone_1 = models.CharField(_("Телефон 1"), max_length=20)
    phone_2 = models.CharField(_("Телефон 2"), max_length=20, blank=True)
    email = models.EmailField(_("Email"))
    address_ru = models.TextField(_("Адрес (рус)"))
    address_en = models.TextField(_("Адрес (англ)"), blank=True)
    telegram = models.URLField(_("Telegram"), blank=True)
    whatsapp = models.URLField(_("WhatsApp"), blank=True)
    instagram = models.URLField(_("Instagram"), blank=True)
    facebook = models.URLField(_("Facebook"), blank=True)
    youtube = models.URLField(_("YouTube"), blank=True)
    work_hours_ru = models.CharField(_("Часы работы (рус)"), max_length=255)
    work_hours_en = models.CharField(_("Часы работы (англ)"), max_length=255, blank=True)
    legal_info_ru = models.TextField(_("Юридическая информация (рус)"), blank=True)
    legal_info_en = models.TextField(_("Юридическая информация (англ)"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("контакт")
        verbose_name_plural = _("контакты")

    def clean(self):
        """Проверка, что только одна запись"""
        if not self.pk and Contact.objects.exists():
            raise ValidationError("Может быть только одна запись с контактами")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Контакты магазина (обновлено: {self.updated_at})"


class Feedback(models.Model):
    """Форма обратной связи"""

    name = models.TextField(_("Имя"), max_length=124)
    phone = models.CharField(_("Телефон"), max_length=20)
    email = models.EmailField(_("Email"))
    message = models.TextField(_("Сообщение"), max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Обратная связь")
        verbose_name_plural = _("Обратная связь")
