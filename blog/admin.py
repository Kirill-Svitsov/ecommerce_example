from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Article, ArticleImage


class ArticleImageInline(admin.TabularInline):
    """Инлайн для изображений статьи"""

    model = ArticleImage
    extra = 1
    fields = ["image", "caption_ru", "caption_en", "sort_order"]
    readonly_fields = ["image_preview"]
    ordering = ["sort_order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = _("Превью")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Админка для статей блога"""

    list_display = [
        "title_ru",
        "slug",
        "is_published",
        "is_main_badge",
        "published_at",
        "created_at",
        "preview_thumbnail",
    ]

    list_filter = ["is_published", "is_main", "created_at", "published_at"]

    search_fields = [
        "title_ru",
        "title_en",
        "short_description_ru",
        "short_description_en",
        "description_ru",
        "description_en",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "slug",
        "sort_order",
        "preview_photo_preview",
        "preview_wide_photo_preview",
    ]

    fieldsets = [
        (
            _("Основное"),
            {"fields": ["title_ru", "title_en", "slug", "is_published", "is_main", "published_at"]},
        ),
        (_("Краткое описание"), {"fields": ["short_description_ru", "short_description_en"]}),
        (
            _("Полное содержание"),
            {"fields": ["description_ru", "description_en"], "classes": ["collapse"]},
        ),
        (
            _("Изображения"),
            {
                "fields": [
                    "preview_photo",
                    "preview_photo_preview",
                    "preview_wide_photo",
                    "preview_wide_photo_preview",
                ]
            },
        ),
        (
            _("Системная информация"),
            {"fields": ["sort_order", "created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    inlines = [ArticleImageInline]

    list_editable = ["is_published"]
    list_per_page = 50
    save_on_top = True

    actions = ["publish_articles", "unpublish_articles", "set_as_main"]

    def is_main_badge(self, obj):
        """Бейдж для главного поста"""
        if obj.is_main:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: '
                '3px 8px; border-radius: 3px; font-size: 12px;">★ ГЛАВНЫЙ</span>'
            )
        return "-"

    is_main_badge.short_description = _("Главный")
    is_main_badge.admin_order_field = "is_main"

    def preview_thumbnail(self, obj):
        """Миниатюра превью"""
        if obj.preview_photo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px;" />',
                obj.preview_photo.url,
            )
        return "-"

    preview_thumbnail.short_description = _("Превью")

    def preview_photo_preview(self, obj):
        """Превью фото"""
        if obj.preview_photo:
            return format_html(
                '<img src="{}" style="max-height: 150px; max-width: 300px; border-radius: 4px;" />',
                obj.preview_photo.url,
            )
        return "-"

    preview_photo_preview.short_description = _("Предпросмотр")

    def preview_wide_photo_preview(self, obj):
        """Превью широкого фото"""
        if obj.preview_wide_photo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 400px; border-radius: 4px;" />',
                obj.preview_wide_photo.url,
            )
        return "-"

    preview_wide_photo_preview.short_description = _("Предпросмотр")

    def publish_articles(self, request, queryset):
        """Опубликовать выбранные статьи"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} статей опубликовано")

    publish_articles.short_description = _("Опубликовать")

    def unpublish_articles(self, request, queryset):
        """Снять с публикации"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} статей снято с публикации")

    unpublish_articles.short_description = _("Снять с публикации")

    def set_as_main(self, request, queryset):
        """Сделать главным постом (только один)"""
        if queryset.count() > 1:
            self.message_user(
                request, "Можно выбрать только одну статью как главную", level="ERROR"
            )
            return

        article = queryset.first()
        if article:
            article.is_main = True
            article.save()
            self.message_user(request, f"Статья '{article.title_ru}' теперь главная")

    set_as_main.short_description = _("Сделать главной")


@admin.register(ArticleImage)
class ArticleImageAdmin(admin.ModelAdmin):
    """Админка для изображений статей"""

    list_display = ["id", "image_preview", "caption_ru", "sort_order", "get_articles"]

    list_filter = ["sort_order"]
    search_fields = ["caption_ru", "caption_en"]
    list_editable = ["sort_order"]
    readonly_fields = ["image_preview"]
    ordering = ["sort_order"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = _("Изображение")

    def get_articles(self, obj):
        """Статья, к которой привязано изображение"""
        return obj.article.title_ru if obj.article else "-"

    get_articles.short_description = _("Используется в")
