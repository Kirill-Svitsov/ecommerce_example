from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Cart, CartItem
from catalog.models import Spec


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Админка корзины"""

    list_display = [
        "user_email",
        "user_name",
        "total_items_display",
        "total_price_display",
        "updated_at",
    ]
    list_filter = ["updated_at", "created_at"]
    search_fields = ["user__email", "user__username", "user__first_name", "user__last_name"]
    readonly_fields = [
        "user",
        "created_at",
        "updated_at",
        "items_list",
        "total_items_display",
        "total_price_display",
    ]
    date_hierarchy = "updated_at"
    ordering = ["-updated_at"]

    fieldsets = (
        (_("Пользователь"), {"fields": ("user",)}),
        (
            _("Содержимое корзины"),
            {"fields": ("items_list", "total_items_display", "total_price_display")},
        ),
        (
            _("Системная информация"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = _("Email")
    user_email.admin_order_field = "user__email"

    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    user_name.short_description = _("Имя")
    user_name.admin_order_field = "user__first_name"

    def total_items_display(self, obj):
        count = obj.get_total_items()
        return format_html(
            '<span style="font-weight: bold; color: #27ae60; font-size: 18px;">{}</span>', count
        )

    total_items_display.short_description = _("Товаров в корзине")

    def total_price_display(self, obj):
        price = obj.get_total_price_rub()
        return format_html(
            '<span style="font-weight: bold; color: #e74c3c; font-size: 18px;">{} ₽</span>', price
        )

    total_price_display.short_description = _("Общая сумма")

    def items_list(self, obj):
        """Отображение списка товаров в корзине"""
        items = obj.items.all().select_related("item", "size")
        if not items:
            return format_html('<span style="color: #95a5a6;">Корзина пуста</span>')

        html = '<div style="max-height: 400px; overflow-y: auto;">'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += """
            <thead>
                <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                    <th style="text-align: left; padding: 8px;">Товар</th>
                    <th style="text-align: center; padding: 8px;">Размер</th>
                    <th style="text-align: center; padding: 8px;">Кол-во</th>
                    <th style="text-align: right; padding: 8px;">Цена</th>
                    <th style="text-align: right; padding: 8px;">Итого</th>
                </tr>
            </thead>
            <tbody>
        """

        for item in items:
            # Получаем характеристики
            specs = Spec.objects.filter(id__in=item.selected_spec_ids)
            specs_html = '<ul style="margin: 0; padding-left: 20px;">'
            for spec in specs:
                specs_html += (
                    f"<li><strong>{spec.name_ru}:"
                    f"</strong> {spec.value_ru} (+{spec.price_modifier_rub} ₽)</li>"
                )
            specs_html += "</ul>"

            if item.size:
                size_str = item.size.value_ru
            else:
                size_str = "-"

            html += f"""
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px;">
                        <strong>{item.item.name_ru}</strong><br>
                        {specs_html}
                    </td>
                    <td style="text-align: center; padding: 8px;">{size_str}</td>
                    <td style="text-align: center; padding: 8px;">{item.quantity}</td>
                    <td style="text-align: right; padding: 8px;">{item.get_price_rub()} ₽</td>
                    <td style="text-align: right; padding: 8px; font-weight: bold; color: #27ae60;">
                        {item.get_subtotal_rub()} ₽
                    </td>
                </tr>
            """

        html += "</tbody></table></div>"
        return format_html(html)

    items_list.short_description = _("Содержимое корзины")

    actions = ["clear_selected_carts"]

    def clear_selected_carts(self, request, queryset):
        """Очистить выбранные корзины"""
        count = 0
        for cart in queryset:
            deleted_count, _ = cart.items.all().delete()
            count += deleted_count
        self.message_user(request, f"Очищено {count} товаров из выбранных корзин")

    clear_selected_carts.short_description = "Очистить выбранные корзины"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Админка товара в корзине"""

    list_display = [
        "item_name",
        "cart_user",
        "size_display",
        "quantity_display",
        "price_display",
        "subtotal_display",
        "added_at",
    ]
    list_filter = ["cart__user", "added_at", ("item__category", admin.RelatedOnlyFieldListFilter)]
    search_fields = [
        "item__name_ru",
        "item__name_en",
        "cart__user__email",
        "cart__user__username",
        "cart__user__first_name",
        "cart__user__last_name",
    ]
    readonly_fields = [
        "cart",
        "item",
        "size",
        "quantity",
        "selected_specs_display",
        "price_display",
        "subtotal_display",
        "added_at",
        "cart_user",
        "item_name",
        "size_display",
        "quantity_display",
    ]
    date_hierarchy = "added_at"
    ordering = ["-added_at"]

    fieldsets = (
        (_("Корзина и товар"), {"fields": ("cart", "cart_user", "item", "item_name")}),
        (_("Параметры товара"), {"fields": ("size_display", "selected_specs_display")}),
        (
            _("Количество и цена"),
            {"fields": ("quantity_display", "price_display", "subtotal_display")},
        ),
        (_("Системная информация"), {"fields": ("added_at",), "classes": ("collapse",)}),
    )

    def cart_user(self, obj):
        return obj.cart.user.email

    cart_user.short_description = _("Пользователь")
    cart_user.admin_order_field = "cart__user__email"

    def item_name(self, obj):
        return obj.item.name_ru

    item_name.short_description = _("Товар")
    item_name.admin_order_field = "item__name_ru"

    def size_display(self, obj):
        if obj.size:
            availability = "✅" if obj.size.is_available else "❌"
            return format_html("{} {}", availability, obj.size.value_ru)
        return format_html('<span style="color: #95a5a6;">-</span>')

    size_display.short_description = _("Размер")

    def quantity_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; font-size: 16px;">{}</span>', obj.quantity
        )

    quantity_display.short_description = _("Количество")

    def price_display(self, obj):
        price = obj.get_price_rub()
        return format_html('<span style="color: #3498db; font-weight: bold;">{} ₽</span>', price)

    price_display.short_description = _("Цена за шт.")

    def subtotal_display(self, obj):
        subtotal = obj.get_subtotal_rub()
        return format_html(
            '<span style="color: #27ae60; font-weight: bold; font-size: 18px;">{} ₽</span>',
            subtotal,
        )

    subtotal_display.short_description = _("Итого")

    def selected_specs_display(self, obj):
        """Отображение выбранных характеристик"""
        specs = Spec.objects.filter(id__in=obj.selected_spec_ids)
        if not specs:
            return format_html('<span style="color: #95a5a6;">Нет характеристик</span>')

        html = '<ul style="margin: 0; padding-left: 20px;">'
        for spec in specs:
            modifier = f"(+{spec.price_modifier_rub} ₽)" if spec.price_modifier_rub != 0 else ""
            html += f"<li><strong>{spec.name_ru}:</strong> {spec.value_ru} {modifier}</li>"
        html += "</ul>"
        return format_html(html)

    selected_specs_display.short_description = _("Выбранные характеристики")

    actions = ["remove_from_cart"]

    def remove_from_cart(self, request, queryset):
        """Удалить выбранные товары из корзины"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Удалено {count} товаров из корзины")

    remove_from_cart.short_description = "Удалить из корзины"
