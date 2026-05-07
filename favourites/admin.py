from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .models import Favourite


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    """Админка для избранного и мудборда"""

    list_display = [
        "user_link",
        "item_link",
        "position",
        "on_moodboard",
        "on_moodboard_badge",
        "moodboard_position",
        "created_at",
    ]

    list_filter = ["on_moodboard", "created_at"]

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "item__name_ru",
        "item__name_en",
    ]

    readonly_fields = ["created_at", "updated_at", "on_moodboard_badge"]

    fieldsets = [
        (None, {"fields": ["user", "item"]}),
        (_("Позиции"), {"fields": ["position", "on_moodboard", "moodboard_position"]}),
        (_("Даты"), {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    list_editable = ["position", "on_moodboard", "moodboard_position"]

    list_per_page = 50

    actions = ["add_to_moodboard", "remove_from_moodboard", "reset_positions"]

    def user_link(self, obj):
        """Ссылка на пользователя в админке"""
        url = reverse("admin:users_user_change", args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)

    user_link.short_description = _("Пользователь")
    user_link.admin_order_field = "user__email"

    def item_link(self, obj):
        """Ссылка на товар в админке"""
        url = reverse("admin:catalog_item_change", args=[obj.item_id])
        return format_html('<a href="{}">{}</a>', url, obj.item.name_ru)

    item_link.short_description = _("Товар")
    item_link.admin_order_field = "item__name_ru"

    def on_moodboard_badge(self, obj):
        """Красивый бейдж для статуса в мудборде"""
        if obj.on_moodboard:
            return format_html(
                '<span style="background-color: #28a745;'
                ' color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">✓</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 8px; border-radius: 3px; font-size: 12px;">✗</span>'
        )

    on_moodboard_badge.short_description = _("В мудборде")
    on_moodboard_badge.admin_order_field = "on_moodboard"

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related("user", "item")

    def add_to_moodboard(self, request, queryset):
        """Добавить выбранные в мудборд"""
        updated = queryset.update(on_moodboard=True)
        self.message_user(request, f"{updated} товаров добавлено в мудборд")

    add_to_moodboard.short_description = _("Добавить в мудборд")

    def remove_from_moodboard(self, request, queryset):
        """Убрать выбранные из мудборда"""
        updated = queryset.update(on_moodboard=False)
        self.message_user(request, f"{updated} товаров убрано из мудборда")

    remove_from_moodboard.short_description = _("Убрать из мудборда")

    def reset_positions(self, request, queryset):
        """Сбросить позиции (установить в 0)"""
        updated = queryset.update(position=0, moodboard_position=0)
        self.message_user(request, f"Позиции сброшены для {updated} записей")

    reset_positions.short_description = _("Сбросить позиции")
