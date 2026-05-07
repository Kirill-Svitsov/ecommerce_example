from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка пользователей"""

    list_display = [
        "email",
        "username",
        "full_name_display",
        "is_active",
        "is_staff",
        "is_subscribed",
        "created_at",
    ]
    list_filter = ["is_active", "is_staff", "is_superuser", "is_subscribed", "created_at"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "last_login"]
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Newsletter"), {"fields": ("is_subscribed",)}),
        (_("Important dates"), {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone",
                    "is_subscribed",
                ),
            },
        ),
    )

    def full_name_display(self, obj):
        return obj.full_name or "-"

    full_name_display.short_description = _("Full Name")
    full_name_display.admin_order_field = "first_name"

    actions = ["activate_users", "deactivate_users", "toggle_subscription"]

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} пользователей активировано")

    activate_users.short_description = "Активировать выбранных"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} пользователей деактивировано")

    deactivate_users.short_description = "Деактивировать выбранных"

    def toggle_subscription(self, request, queryset):
        subscribed = queryset.filter(is_subscribed=True).count()
        if subscribed > queryset.count() / 2:
            updated = queryset.update(is_subscribed=False)
            self.message_user(request, f"{updated} пользователей отписаны от рассылки")
        else:
            updated = queryset.update(is_subscribed=True)
            self.message_user(request, f"{updated} пользователей подписаны на рассылку")

    toggle_subscription.short_description = "Переключить подписку"
