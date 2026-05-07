from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

from .models import (
    Category,
    Author,
    Item,
    Size,
    Spec,
    SpecCategory,
    ItemPhoto,
    Service,
    ServicePhoto,
    Discount,
    SpecPhoto,
)


class SizeInline(admin.TabularInline):
    model = Size
    fk_name = "item"
    extra = 1
    fields = [
        "value_ru",
        "value_en",
        "price_multiplier",
        "override_price_rub",
        "is_available",
        "is_custom",
        "sort_order",
    ]
    ordering = ["sort_order"]


class SpecInline(admin.TabularInline):
    model = Spec
    fk_name = "item"
    extra = 1
    fields = ["name_ru", "category", "value_ru", "price_modifier_rub", "sort_order"]
    ordering = ["sort_order"]


class ItemPhotoInline(admin.TabularInline):
    model = ItemPhoto
    fk_name = "item"
    extra = 1
    fields = ["image", "caption_ru", "is_preview", "sort_order"]
    readonly_fields = ["image_preview"]
    ordering = ["sort_order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Превью"


class ServicePhotoInline(admin.TabularInline):
    model = ServicePhoto
    fk_name = "service"
    extra = 1
    fields = ["image", "caption_ru", "is_preview", "sort_order"]
    readonly_fields = ["image_preview"]
    ordering = ["sort_order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Превью"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name_ru", "slug", "parent", "items_count", "is_active", "sort_order"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name_ru", "name_en", "slug"]
    prepopulated_fields = {"slug": ["name_ru"]}
    ordering = ["sort_order", "name_ru"]
    list_editable = ["is_active", "sort_order"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (_("Основное"), {"fields": ("name_ru", "name_en", "slug", "parent")}),
        (_("Описание"), {"fields": ("description_ru", "description_en"), "classes": ("collapse",)}),
        (_("Настройки"), {"fields": ("is_active", "sort_order", "created_at", "updated_at")}),
    )

    def items_count(self, obj):
        count = obj.items.count()
        return format_html("<strong>{}</strong>", count)

    items_count.short_description = _("Товаров")
    items_count.admin_order_field = "items_count"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(items_count=Count("items", filter=Q(items__is_active=True)))


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name_ru", "slug", "photo_preview", "items_count"]
    search_fields = ["name_ru", "name_en", "slug"]
    prepopulated_fields = {"slug": ["name_ru"]}
    readonly_fields = ["created_at", "updated_at", "photo_preview"]

    fieldsets = (
        (_("Основное"), {"fields": ("name_ru", "name_en", "slug")}),
        (_("Биография"), {"fields": ("bio_ru", "bio_en"), "classes": ("collapse",)}),
        (_("Фото"), {"fields": ("photo", "photo_preview")}),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: '
                '150px; max-width: 150px; border-radius: 8px; object-fit: cover;" />',
                obj.photo.url,
            )
        return "-"

    photo_preview.short_description = _("Превью")

    def items_count(self, obj):
        return obj.item_set.filter(is_active=True).count()

    items_count.short_description = _("Товаров")


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = [
        "name_ru",
        "value_display",
        "type",
        "valid_from",
        "valid_to",
        "is_active",
        "applies_to",
    ]
    list_filter = ["type", "is_active", "valid_from", "valid_to"]
    search_fields = ["name_ru", "name_en", "sku"]
    filter_horizontal = ["categories", "items"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "valid_from"

    fieldsets = (
        (_("Основное"), {"fields": ("name_ru", "name_en", "value", "type")}),
        (_("Период действия"), {"fields": ("valid_from", "valid_to", "is_active")}),
        (
            _("Применение"),
            {
                "fields": ("categories", "items"),
                "description": "Выберите категории ИЛИ конкретные товары",
            },
        ),
    )

    def value_display(self, obj):
        if obj.type == "percent":
            return format_html('<span style="color: #e74c3c;">{}%</span>', obj.value)
        return format_html('<span style="color: #3498db;">{} ₽</span>', obj.value)

    value_display.short_description = _("Значение")

    def applies_to(self, obj):
        cats = obj.categories.count()
        items = obj.items.count()
        parts = []
        if cats:
            parts.append(f"Категории: {cats}")
        if items:
            parts.append(f"Товары: {items}")
        return ", ".join(parts) or "-"

    applies_to.short_description = _("Применяется к")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "name_ru",
        "slug",
        "category",
        "author",
        "base_price_display",
        "availability",
        "is_art",
        "art_status",
        "is_active",
        "created_at",
    ]
    list_filter = ["category", "author", "is_art", "is_active", "availability", "created_at"]
    search_fields = [
        "name_ru",
        "name_en",
        "description_ru",
        "description_en",
        "art_description_ru",
        "art_description_en",
        "material",
        "technique",
    ]
    prepopulated_fields = {"slug": ["name_ru"]}
    list_editable = ["is_active"]
    readonly_fields = ["created_at", "updated_at", "preview_photos_display", "photos_display"]
    inlines = [SizeInline, SpecInline, ItemPhotoInline]
    date_hierarchy = "created_at"
    save_on_top = True
    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    "name_ru",
                    "name_en",
                    "slug",
                    "category",
                    "author",
                    "is_art",
                    "is_active",
                    "sort_order",
                    "art_size",
                )
            },
        ),
        (
            _("Общее описание"),
            {
                "fields": ("description_ru", "description_en"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Описание АРТа"),
            {
                "fields": ("art_description_ru", "art_description_en"),
                "classes": ("collapse",),
                "description": _("Заполняется только если товар является АРТом"),
            },
        ),
        (_("Цены"), {"fields": ("base_price_rub", "base_price_usd", "is_price_hidden")}),
        (
            _("Изображения"),
            {"fields": ("image_2d", "image_3d", "preview_photos_display", "photos_display")},
        ),
        (
            _("Системная информация"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def base_price_display(self, obj):
        return format_html('<strong style="color: #27ae60;">{} ₽</strong>', obj.base_price_rub)

    base_price_display.short_description = _("Цена")
    base_price_display.admin_order_field = "base_price_rub"

    def art_status(self, obj):
        """Отображение статуса АРТа с описанием"""
        if obj.is_art:
            has_desc = bool(obj.art_description_ru or obj.art_description_en)
            if has_desc:
                preview = (obj.art_description_ru or obj.art_description_en)[:50]
                if len(preview) > 47:
                    preview = preview[:47] + "..."
                return format_html(
                    '<span style="color: #9b59b6;">✓ АРТ</span><br/>'
                    '<small style="color: #7f8c8d;">{}</small>',
                    preview,
                )
            return format_html(
                '<span style="color: #e67e22;">⚠ АРТ</span><br/>'
                '<small style="color: #e74c3c;">нет описания</small>'
            )
        return format_html('<span style="color: #7f8c8d;">—</span>')

    art_status.short_description = _("Статус АРТа")
    art_status.admin_order_field = "is_art"

    def preview_photos_display(self, obj):
        if obj.preview_photos:
            images = "".join(
                [
                    f'<img src="{url}" style="max-height: 80px; max-width: '
                    f'80px; margin: 2px; border-radius: 4px;" />'
                    for url in obj.preview_photos[:3]
                ]
            )
            return format_html(images)
        return "-"

    preview_photos_display.short_description = _("Превью")

    def photos_display(self, obj):
        count = len(obj.photos) if obj.photos else 0
        return format_html('<span style="color: #7f8c8d;">{} фото</span>', count)

    photos_display.short_description = _("Фото")

    actions = ["activate_items", "deactivate_items", "mark_as_art", "unmark_as_art"]

    def activate_items(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} товаров активировано")

    activate_items.short_description = "Активировать"

    def deactivate_items(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} товаров деактивировано")

    deactivate_items.short_description = "Деактивировать"

    def mark_as_art(self, request, queryset):
        updated = queryset.update(is_art=True)
        self.message_user(
            request,
            f"{updated} товаров помечено как АРТ. Не забудьте заполнить описание АРТа!",
            level="WARNING",
        )

    mark_as_art.short_description = "Пометить как АРТ"

    def unmark_as_art(self, request, queryset):
        updated = queryset.update(is_art=False)
        self.message_user(request, f"{updated} товаров снято с отметки АРТ")

    unmark_as_art.short_description = "Снять отметку АРТ"

    def save_model(self, request, obj, form, change):
        """Валидация при сохранении через админку"""
        if obj.is_art and not obj.art_description_ru:
            self.message_user(
                request,
                "Внимание: товар помечен как АРТ, но отсутствует описание на русском языке!",
                level="ERROR",
            )
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Показываем ВСЕ товары, включая неактивные"""
        qs = super().get_queryset(request)
        # Убираем фильтрацию по is_active, если она есть в менеджере
        return qs

    def get_search_results(self, request, queryset, search_term):
        """Поиск по всем товарам, включая неактивные"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name_ru",
        "slug",
        "price_display",
        "is_price_hidden",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "is_price_hidden", "created_at"]
    search_fields = ["name_ru", "name_en", "description_ru"]
    prepopulated_fields = {"slug": ["name_ru"]}
    list_editable = ["is_active"]
    readonly_fields = ["created_at", "updated_at", "preview_photos_display", "photos_display"]
    inlines = [ServicePhotoInline]
    filter_horizontal = ["discounts"]
    save_on_top = True

    fieldsets = (
        (_("Основное"), {"fields": ("name_ru", "name_en", "slug", "is_active", "sort_order")}),
        (
            _("Описание"),
            {
                "fields": (
                    "short_description_ru",
                    "short_description_en",
                    "description_ru",
                    "description_en",
                )
            },
        ),
        (_("Цены"), {"fields": ("price_rub", "price_usd", "is_price_hidden")}),
        (_("Изображения"), {"fields": ("preview_photos_display", "photos_display")}),
        (_("Скидки"), {"fields": ("discounts",), "classes": ("collapse",)}),
        (
            _("Системная информация"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def price_display(self, obj):
        if obj.is_price_hidden:
            return format_html('<span style="color: #95a5a6;">Скрыто</span>')
        if obj.price_rub:
            return format_html('<strong style="color: #27ae60;">{} ₽</strong>', obj.price_rub)
        return "-"

    price_display.short_description = _("Цена")

    def preview_photos_display(self, obj):
        if obj.preview_photos:
            images = "".join(
                [
                    f'<img src="{url}" style="max-height: 80px; max-width: '
                    f'80px; margin: 2px; border-radius: 4px;" />'
                    for url in obj.preview_photos[:3]
                ]
            )
            return format_html(images)
        return "-"

    preview_photos_display.short_description = _("Превью")

    def photos_display(self, obj):
        count = len(obj.photos) if obj.photos else 0
        return format_html('<span style="color: #7f8c8d;">{} фото</span>', count)

    photos_display.short_description = _("Фото")


@admin.register(SpecCategory)
class SpecCategoryAdmin(admin.ModelAdmin):
    list_display = ["name_ru", "name_en", "sort_order"]
    list_editable = ["sort_order"]
    search_fields = ["name_ru", "name_en"]
    ordering = ["sort_order", "name_ru"]


@admin.register(Spec)
class SpecAdmin(admin.ModelAdmin):
    list_display = ["name_ru", "category", "value_ru", "price_display", "is_custom", "item"]
    list_filter = ["category", "item", "is_custom"]
    search_fields = ["name_ru", "value_ru", "item__name_ru"]
    ordering = ["item", "sort_order"]
    list_editable = ["is_custom"]

    def price_display(self, obj):
        if obj.is_custom:
            return format_html('<span style="color: #9b59b6;"> Индивидуально</span>')
        if obj.price_modifier_rub > 0:
            return format_html('<span style="color: #27ae60;">+{} ₽</span>', obj.price_modifier_rub)
        elif obj.price_modifier_rub < 0:
            return format_html('<span style="color: #e74c3c;">{} ₽</span>', obj.price_modifier_rub)
        return "0 ₽"

    price_display.short_description = _("Цена")


@admin.register(SpecPhoto)
class SpecPhotoAdmin(admin.ModelAdmin):
    list_display = ["spec", "image_preview", "caption_ru", "sort_order"]
    list_filter = ["spec__category", "spec__item"]
    search_fields = ["spec__name_ru", "spec__value_ru", "caption_ru"]
    readonly_fields = ["image_preview"]
    ordering = ["spec", "sort_order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Превью"


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = [
        "item",
        "value_ru",
        "value_en",
        "price_display",
        "is_available",
        "is_custom",
    ]
    list_filter = ["is_available", "is_custom", "item__category"]
    search_fields = ["value_ru", "value_en", "item__name_ru"]
    list_editable = ["is_available", "is_custom"]
    ordering = ["item", "sort_order"]

    def price_display(self, obj):
        """Улучшенное отображение цены с учетом кастомных размеров"""
        if obj.is_custom:
            return format_html('<span style="color: #9b59b6;">Индивидуально</span>')
        if obj.override_price_rub:
            return format_html(
                '<span style="color: #3498db; font-weight: bold;">{} ₽</span>',
                obj.override_price_rub,
            )
        if obj.price_multiplier != 1.0:
            return format_html(
                '<span style="color: #27ae60;">×{}</span>',
                obj.price_multiplier,
            )
        return format_html('<span style="color: #7f8c8d;">Базовая</span>')

    price_display.short_description = _("Цена")
    price_display.admin_order_field = "override_price_rub"


@admin.register(ItemPhoto)
class ItemPhotoAdmin(admin.ModelAdmin):
    list_display = ["item", "image_preview", "caption_ru", "is_preview", "sort_order"]
    list_filter = ["is_preview", "item__category"]
    search_fields = ["item__name_ru", "caption_ru"]
    readonly_fields = ["image_preview"]
    ordering = ["item", "sort_order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Превью"


@admin.register(ServicePhoto)
class ServicePhotoAdmin(admin.ModelAdmin):
    list_display = ["service", "image_preview", "caption_ru", "is_preview", "sort_order"]
    list_filter = ["is_preview", "service"]
    search_fields = ["service__name_ru", "caption_ru"]
    readonly_fields = ["image_preview"]
    ordering = ["service", "sort_order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Превью"
