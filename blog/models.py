from django.db import models
from django.utils.translation import gettext_lazy as _


def transliterate(text):
    """Простая транслитерация кириллицы в латиницу"""
    mapping = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        " ": "-",
        ",": "",
        ".": "",
        "!": "",
        "?": "",
        '"': "",
        "'": "",
    }

    text = text.lower()
    result = []
    for char in text:
        result.append(mapping.get(char, char))
    return "".join(result)


class ArticleImage(models.Model):
    """Изображение для статьи"""

    article = models.ForeignKey(
        "Article", on_delete=models.CASCADE, related_name="images", verbose_name=_("статья")
    )
    image = models.ImageField(_("Изображение"), upload_to="blog/images/")
    caption_ru = models.CharField(_("Подпись (рус)"), max_length=255, blank=True)
    caption_en = models.CharField(_("Подпись (англ)"), max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("изображение статьи")
        verbose_name_plural = _("изображения статей")
        ordering = ["sort_order"]


class Article(models.Model):
    """Статья блога"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(_("Дата публикации"), null=True, blank=True)
    # Мультиязычные поля
    title_ru = models.CharField(_("Заголовок (рус)"), max_length=500)
    title_en = models.CharField(_("Заголовок (англ)"), max_length=500, blank=True)
    short_description_ru = models.TextField(_("Краткое описание (рус)"), blank=True)
    short_description_en = models.TextField(_("Краткое описание (англ)"), blank=True)
    description_ru = models.TextField(_("Содержание (рус)"), blank=True)
    description_en = models.TextField(_("Содержание (англ)"), blank=True)
    # Изображения
    preview_photo = models.ImageField(
        _("Превью"), upload_to="blog/previews/", null=True, blank=True
    )
    preview_wide_photo = models.ImageField(
        _("Широкое превью"), upload_to="blog/previews/wide/", null=True, blank=True
    )
    slug = models.SlugField(_("Slug"), unique=True, max_length=255, db_index=True)
    # Статус и порядок
    is_published = models.BooleanField(_("Опубликовано"), default=False)
    is_main = models.BooleanField(_("Главный пост"), default=False)
    sort_order = models.PositiveIntegerField(_("Порядок"), default=1)

    class Meta:
        verbose_name = _("статья")
        verbose_name_plural = _("статьи")
        ordering = ["sort_order", "-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_published", "published_at"]),
            models.Index(fields=["is_main"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return self.title_ru

    def save(self, *args, **kwargs):
        if not self.slug:
            base = transliterate(self.title_ru)
            self.slug = base
            counter = 1
            original_slug = self.slug
            if not self.pk:
                while Article.objects.filter(slug=self.slug).exists():
                    self.slug = f"{original_slug}-{counter}"
                    counter += 1
            else:
                while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                    self.slug = f"{original_slug}-{counter}"
                    counter += 1
        if self.is_main:
            if self.pk:
                Article.objects.filter(is_main=True).exclude(pk=self.pk).update(
                    is_main=False, sort_order=1
                )
            else:
                Article.objects.filter(is_main=True).update(is_main=False, sort_order=1)
            self.sort_order = 0
        else:
            self.sort_order = 1
        super().save(*args, **kwargs)
