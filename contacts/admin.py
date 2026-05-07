from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Админка для контактов магазина"""

    list_display = ["id", "phone_1", "email", "telegram_link", "instagram_link", "updated_at"]

    fieldsets = [
        (_("Телефоны"), {"fields": ["phone_1", "phone_2"]}),
        (_("Email"), {"fields": ["email"]}),
        (_("Адрес"), {"fields": ["address_ru", "address_en"]}),
        (
            _("Социальные сети"),
            {"fields": ["telegram", "whatsapp", "instagram", "facebook", "youtube"]},
        ),
        (_("Часы работы"), {"fields": ["work_hours_ru", "work_hours_en"]}),
        (
            _("Юридическая информация"),
            {"fields": ["legal_info_ru", "legal_info_en"], "classes": ["collapse"]},
        ),
        (
            _("Системная информация"),
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    readonly_fields = ["created_at", "updated_at", "social_links_preview"]

    def telegram_link(self, obj):
        if obj.telegram:
            return format_html('<a href="{}" target="_blank">Telegram</a>', obj.telegram)
        return "-"

    telegram_link.short_description = _("Telegram")

    def instagram_link(self, obj):
        if obj.instagram:
            return format_html('<a href="{}" target="_blank">Instagram</a>', obj.instagram)
        return "-"

    instagram_link.short_description = _("Instagram")

    def social_links_preview(self, obj):
        """Предпросмотр всех ссылок"""
        links = []
        if obj.telegram:
            links.append(f'<a href="{obj.telegram}" target="_blank">Telegram</a>')
        if obj.whatsapp:
            links.append(f'<a href="{obj.whatsapp}" target="_blank">WhatsApp</a>')
        if obj.instagram:
            links.append(f'<a href="{obj.instagram}" target="_blank">Instagram</a>')
        if obj.facebook:
            links.append(f'<a href="{obj.facebook}" target="_blank">Facebook</a>')
        if obj.youtube:
            links.append(f'<a href="{obj.youtube}" target="_blank">YouTube</a>')

        if links:
            return format_html("<br>".join(links))
        return "-"

    social_links_preview.short_description = _("Ссылки")

    def has_add_permission(self, request):
        """Запрещаем добавлять больше одной записи"""
        if Contact.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление единственной записи"""
        return False
