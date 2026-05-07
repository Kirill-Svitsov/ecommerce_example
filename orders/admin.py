from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .models import Order, OrderItem, OrderService, DeliveryAddress, PromoCode


class OrderItemInline(admin.TabularInline):
    """Товары в заказе"""

    model = OrderItem
    extra = 0
    readonly_fields = [
        "item_link",
        "name",
        "sku",
        "size_value_ru",
        "quantity",
        "price_rub",
        "total_rub",
    ]
    fields = ["item_link", "name", "size_value_ru", "quantity", "price_rub", "total_rub"]
    can_delete = False

    def item_link(self, obj):
        if obj.item:
            url = reverse("admin:catalog_item_change", args=[obj.item_id])
            return format_html('<a href="{}">{}</a>', url, obj.item.name_ru)
        return obj.name

    item_link.short_description = _("Товар")
    item_link.admin_order_field = "item"


class OrderServiceInline(admin.TabularInline):
    """Услуги в заказе"""

    model = OrderService
    extra = 0
    readonly_fields = ["service_link", "name", "quantity", "price_rub", "total_rub"]
    fields = ["service_link", "name", "quantity", "price_rub", "total_rub"]
    can_delete = False

    def service_link(self, obj):
        if obj.service:
            url = reverse("admin:catalog_service_change", args=[obj.service_id])
            return format_html('<a href="{}">{}</a>', url, obj.service.name_ru)
        return obj.name

    service_link.short_description = _("Услуга")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "user_email",
        "full_name",
        "status_badge",
        "payment_status_badge",
        "total_rub_display",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "payment_method", "created_at"]
    search_fields = ["order_number", "email", "phone", "full_name"]
    readonly_fields = [
        "order_number",
        "created_at",
        "updated_at",
        "paid_at",
        "subtotal_rub",
        "subtotal_usd",
        "discount_rub",
        "discount_usd",
        "total_rub",
        "total_usd",
        "promo_discount_rub",
        "promo_discount_usd",
    ]
    fieldsets = [
        (
            _("Основное"),
            {
                "fields": [
                    "order_number",
                    "user",
                    "status",
                    "payment_status",
                    "payment_method",
                    "payment_id",
                ]
            },
        ),
        (_("Контакты"), {"fields": ["email", "phone", "full_name"]}),
        (
            _("Доставка"),
            {
                "fields": [
                    "delivery_address",
                    "delivery_address_text",
                    "delivery_instructions",
                    "delivery_cost_rub",
                    "delivery_cost_usd",
                ]
            },
        ),
        (
            _("Цены"),
            {
                "fields": [
                    "subtotal_rub",
                    "subtotal_usd",
                    "discount_rub",
                    "discount_usd",
                    "total_rub",
                    "total_usd",
                ]
            },
        ),
        (
            _("Промокод"),
            {
                "fields": [
                    "promo_code",
                    "promo_code_text",
                    "promo_discount_rub",
                    "promo_discount_usd",
                ],
                "classes": ["collapse"],
            },
        ),
        (_("Комментарии"), {"fields": ["customer_comment"]}),
        (_("Даты"), {"fields": ["created_at", "updated_at", "paid_at"]}),
    ]
    inlines = [OrderItemInline, OrderServiceInline]

    actions = ["confirm_orders", "mark_as_paid", "cancel_orders"]

    def user_email(self, obj):
        if obj.user:
            url = reverse("admin:users_user_change", args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return obj.email

    user_email.short_description = _("Пользователь")
    user_email.admin_order_field = "user__email"

    def status_badge(self, obj):
        colors = {
            "new": "#6c757d",
            "confirmed": "#17a2b8",
            "paid": "#28a745",
            "assembling": "#ffc107",
            "shipped": "#007bff",
            "delivered": "#28a745",
            "cancelled": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; '
            'color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Статус")

    def payment_status_badge(self, obj):
        colors = {
            "pending": "#6c757d",
            "paid": "#28a745",
            "failed": "#dc3545",
            "refunded": "#ffc107",
        }
        color = colors.get(obj.payment_status, "#6c757d")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display(),
        )

    payment_status_badge.short_description = _("Оплата")

    def total_rub_display(self, obj):
        return format_html('<span style="font-weight: bold;">{} ₽</span>', obj.total_rub)

    total_rub_display.short_description = _("Сумма")
    total_rub_display.admin_order_field = "total_rub"

    def confirm_orders(self, request, queryset):
        updated = queryset.filter(status="new").update(status="confirmed")
        self.message_user(request, f"{updated} заказов подтверждено")

    confirm_orders.short_description = _("Подтвердить выбранные заказы")

    def mark_as_paid(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(payment_status="pending").update(
            payment_status="paid", paid_at=timezone.now()
        )
        self.message_user(request, f"{updated} заказов отмечено как оплачено")

    mark_as_paid.short_description = _("Отметить как оплаченные")

    def cancel_orders(self, request, queryset):
        cancellable = queryset.filter(status__in=["new", "confirmed"])
        count = cancellable.count()
        cancellable.update(status="cancelled")
        self.message_user(request, f"{count} заказов отменено")

    cancel_orders.short_description = _("Отменить выбранные заказы")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order_link", "item_name", "quantity", "price_rub", "total_rub"]
    list_filter = ["order__status"]
    search_fields = ["order__order_number", "name", "sku"]
    readonly_fields = [
        "order",
        "item",
        "name",
        "sku",
        "size_value_ru",
        "selected_specs_snapshot",
        "image",
        "quantity",
        "price_rub",
        "price_usd",
        "total_rub",
        "total_usd",
    ]

    def order_link(self, obj):
        url = reverse("admin:orders_order_change", args=[obj.order_id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)

    order_link.short_description = _("Заказ")

    def item_name(self, obj):
        if obj.item:
            return obj.item.name_ru
        return obj.name

    item_name.short_description = _("Товар")


@admin.register(OrderService)
class OrderServiceAdmin(admin.ModelAdmin):
    list_display = ["order_link", "service_name", "quantity", "price_rub", "total_rub"]
    list_filter = ["order__status"]
    search_fields = ["order__order_number", "name"]
    readonly_fields = [
        "order",
        "service",
        "name",
        "image",
        "quantity",
        "price_rub",
        "price_usd",
        "total_rub",
        "total_usd",
    ]

    def order_link(self, obj):
        url = reverse("admin:orders_order_change", args=[obj.order_id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)

    order_link.short_description = _("Заказ")

    def service_name(self, obj):
        if obj.service:
            return obj.service.name_ru
        return obj.name

    service_name.short_description = _("Услуга")


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ["user", "label", "short_address", "is_default", "created_at"]
    list_filter = ["is_default", "has_elevator", "requires_assemblers"]
    search_fields = ["user__email", "address", "comment"]
    readonly_fields = ["created_at"]
    fieldsets = [
        (None, {"fields": ["user", "label", "is_default"]}),
        (_("Адрес"), {"fields": ["address", "entrance", "floor", "apartment", "comment"]}),
        (_("Дополнительно"), {"fields": ["has_elevator", "requires_assemblers"]}),
        (_("Даты"), {"fields": ["created_at"]}),
    ]

    def short_address(self, obj):
        return obj.full_address()[:50] + ("..." if len(obj.full_address()) > 50 else "")

    short_address.short_description = _("Адрес")


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "description",
        "discount_display",
        "valid_until",
        "is_active",
        "used_count",
    ]
    list_filter = ["is_active", "valid_until"]
    search_fields = ["code", "description"]
    readonly_fields = ["used_count"]
    fieldsets = [
        (None, {"fields": ["code", "description", "is_active"]}),
        (
            _("Скидка"),
            {"fields": ["discount_percent", "discount_amount_rub", "discount_amount_usd"]},
        ),
        (_("Ограничения"), {"fields": ["valid_until", "max_uses", "used_count"]}),
    ]

    def discount_display(self, obj):
        if obj.discount_percent:
            return f"{obj.discount_percent}%"
        elif obj.discount_amount_rub:
            return f"{obj.discount_amount_rub} ₽"
        elif obj.discount_amount_usd:
            return f"{obj.discount_amount_usd} $"
        return "-"

    discount_display.short_description = _("Скидка")

    actions = ["activate_promo_codes", "deactivate_promo_codes"]

    def activate_promo_codes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} промокодов активировано")

    activate_promo_codes.short_description = _("Активировать")

    def deactivate_promo_codes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} промокодов деактивировано")

    deactivate_promo_codes.short_description = _("Деактивировать")
