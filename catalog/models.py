from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseCatalogModel(models.Model):
    """Базовая модель с полями создания и обновления"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseCatalogModel):
    """Категория каталога (может быть вложенной)"""

    name_ru = models.CharField(_("название (рус)"), max_length=255)
    name_en = models.CharField(_("название (англ)"), max_length=255, blank=True)
    description_ru = models.TextField(_("описание (рус)"), blank=True)
    description_en = models.TextField(_("описание (англ)"), blank=True)
    slug = models.SlugField(_("slug"), unique=True, max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("родительская категория"),
    )
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)
    is_active = models.BooleanField(_("активна"), default=True)

    class Meta:
        verbose_name = _("категория")
        verbose_name_plural = _("категории")
        ordering = ["sort_order", "name_ru"]

    def __str__(self):
        return self.name_ru


class Author(BaseCatalogModel):
    """Автор (для артов/товаров)"""

    name_ru = models.CharField(_("имя (рус)"), max_length=255)
    name_en = models.CharField(_("имя (англ)"), max_length=255, blank=True)
    bio_ru = models.TextField(_("биография (рус)"), blank=True)
    bio_en = models.TextField(_("биография (англ)"), blank=True)
    slug = models.SlugField(_("slug"), unique=True, max_length=255)
    photo = models.ImageField(_("фотография"), upload_to="authors/", null=True, blank=True)

    class Meta:
        verbose_name = _("автор")
        verbose_name_plural = _("авторы")

    def __str__(self):
        return self.name_ru


class Discount(BaseCatalogModel):
    """Скидка (процент или фиксированная сумма)"""

    TYPE_CHOICES = [
        ("percent", _("процент")),
        ("fixed", _("фиксированная")),
    ]

    name_ru = models.CharField(_("название (рус)"), max_length=255)
    name_en = models.CharField(_("название (англ)"), max_length=255, blank=True)
    value = models.DecimalField(_("значение"), max_digits=10, decimal_places=2)
    type = models.CharField(_("тип"), max_length=10, choices=TYPE_CHOICES, default="percent")
    valid_from = models.DateTimeField(_("действует с"), null=True, blank=True)
    valid_to = models.DateTimeField(_("действует до"), null=True, blank=True)
    is_active = models.BooleanField(_("активна"), default=True)

    categories = models.ManyToManyField(
        Category, blank=True, related_name="discounts", verbose_name=_("категории")
    )
    items = models.ManyToManyField(
        "Item", blank=True, related_name="discounts", verbose_name=_("товары")
    )

    class Meta:
        verbose_name = _("скидка")
        verbose_name_plural = _("скидки")

    def __str__(self):
        return f"{self.name_ru} ({self.value}{'%' if self.type == 'percent' else ' ₽'})"


class Item(BaseCatalogModel):
    """Элемент каталога (товар)"""

    STATUS_CHOICES = [
        ("in_stock", "В наличии"),
        ("custom", "Срок изготовления 2 месяца"),
    ]
    AVAILABILITY_CHOICES = [
        ("in_stock", "В наличии"),
        ("preorder", "Под заказ"),
        ("custom", "Срок изготовления 2 месяца"),
        ("out_of_stock", "Нет в наличии"),
    ]

    name_ru = models.CharField(_("название (рус)"), max_length=500)
    name_en = models.CharField(_("название (англ)"), max_length=500, blank=True)
    sku = models.CharField(_("артикул"), max_length=100, blank=True, db_index=True)
    description_ru = models.TextField(_("описание (рус)"), blank=True)
    description_en = models.TextField(_("описание (англ)"), blank=True)
    is_art = models.BooleanField(_("Является ли АРТом"), default=False)
    art_description_ru = models.TextField(
        _("описание АРТа (рус)"),
        blank=True,
        help_text=_("Заполняется только если товар является АРТом"),
    )
    art_description_en = models.TextField(
        _("описание АРТа (англ)"),
        blank=True,
        help_text=_("Заполняется только если товар является АРТом"),
    )
    slug = models.SlugField(_("slug"), unique=True, max_length=255, db_index=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="items", verbose_name=_("категория")
    )
    author = models.ForeignKey(
        Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("автор")
    )
    base_price_rub = models.DecimalField(
        _("базовая цена (руб)"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Цена для базового размера (коэффициент 1.0)"),
    )
    base_price_usd = models.DecimalField(
        _("базовая цена (USD)"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Цена для базового размера (коэффициент 1.0)"),
    )
    is_price_hidden = models.BooleanField(_("скрыть цену"), default=False)
    image_2d = models.ImageField(_("2D-чертёж"), upload_to="items/2d/", null=True, blank=True)
    image_3d = models.FileField(_("3D-модель"), upload_to="items/3d/", null=True, blank=True)
    preview_photos = models.JSONField(_("превью"), default=list, blank=True)
    photos = models.JSONField(_("фотографии"), default=list, blank=True)
    is_active = models.BooleanField(_("активен"), default=True, db_index=True)
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)
    status = models.CharField(
        _("Статус"), max_length=20, choices=STATUS_CHOICES, default="in_stock"
    )
    availability = models.CharField(
        _("наличие"),
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default="in_stock",
        db_index=True,
    )
    lead_time_days = models.PositiveIntegerField(
        _("срок изготовления (дни)"),
        null=True,
        blank=True,
        help_text=_("Заполняется если availability = 'custom' или 'preorder'"),
    )

    # Поля для АРТ
    art_size = models.CharField(
        _("размер арта"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Размер арта (только для АРТ)"),
    )
    creation_year = models.PositiveIntegerField(
        _("год создания"),
        null=True,
        blank=True,
        help_text=_("Год создания (только для АРТ)"),
    )
    weight = models.DecimalField(
        _("вес (кг)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Вес в килограммах (только для АРТ)"),
    )
    material = models.CharField(
        _("материал"),
        max_length=255,
        blank=True,
        help_text=_("Материал (только для АРТ)"),
    )
    technique = models.CharField(
        _("техника"),
        max_length=255,
        blank=True,
        help_text=_("Техника исполнения (только для АРТ)"),
    )

    class Meta:
        verbose_name = _("товар")
        verbose_name_plural = _("товары")
        ordering = ["sort_order", "name_ru"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self):
        return self.name_ru

    def get_base_price(self, currency="rub"):
        return self.base_price_usd if currency == "usd" else self.base_price_rub

    def get_active_discount(self):
        from django.utils import timezone

        now = timezone.now()
        item_discount = self.discounts.filter(
            is_active=True, valid_from__lte=now, valid_to__gte=now
        ).first()
        if item_discount:
            return item_discount
        if self.category:
            return self.category.discounts.filter(
                is_active=True, valid_from__lte=now, valid_to__gte=now
            ).first()
        return None

    def calculate_price(self, size=None, selected_specs=None, currency="rub"):
        price = self.base_price_rub if currency == "rub" else self.base_price_usd
        # Проверяем, есть ли кастомный размер
        has_custom_size = size and size.is_custom if size else False
        if selected_specs:
            for spec in selected_specs:
                if spec.is_custom:
                    continue
                price += spec.price_modifier_rub if currency == "rub" else spec.price_modifier_usd
        if size and not size.is_custom:
            if size.override_price_rub is not None and currency == "rub":
                price = size.override_price_rub
            elif size.override_price_usd is not None and currency == "usd":
                price = size.override_price_usd
            else:
                price *= size.price_multiplier
        discount = self.get_active_discount()
        if discount:
            if discount.type == "percent":
                price *= 1 - discount.value / 100
            else:
                price = max(price - discount.value, 0)
        # Проверяем, есть ли кастомные specs или кастомный размер
        has_custom_specs = any(spec.is_custom for spec in (selected_specs or []))
        if has_custom_specs or has_custom_size:
            return 0
        return round(price, 2)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            base_name = self.name_ru or self.name_en
            base = slugify(base_name)
            slug = base
            counter = 1
            while Item.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Size(BaseCatalogModel):
    """Размер товара с коэффициентом к базовой цене"""

    value_ru = models.CharField(_("значение (рус)"), max_length=50)
    value_en = models.CharField(_("значение (англ)"), max_length=50, blank=True)
    price_multiplier = models.DecimalField(
        _("коэффициент цены"), max_digits=5, decimal_places=2, default=1.0
    )
    override_price_rub = models.DecimalField(
        _("фикс. цена (руб)"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    override_price_usd = models.DecimalField(
        _("фикс. цена (USD)"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="sizes", verbose_name=_("товар")
    )
    is_available = models.BooleanField(_("доступен"), default=True)
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)
    is_custom = models.BooleanField(
        _("кастомный размер"),
        default=False,
        help_text=_("Цена рассчитывается менеджером индивидуально"),
    )

    class Meta:
        verbose_name = _("размер")
        verbose_name_plural = _("размеры")
        ordering = ["sort_order", "value_ru"]
        unique_together = ["item", "value_ru"]

    def __str__(self):
        return f"{self.item.name_ru} - {self.value_ru}"

    def get_price_rub(self):
        if self.is_custom:
            return 0
        if self.override_price_rub is not None:
            return self.override_price_rub
        return self.item.base_price_rub * self.price_multiplier

    def get_price_usd(self):
        if self.is_custom:
            return 0
        if self.override_price_usd is not None:
            return self.override_price_usd
        return self.item.base_price_usd * self.price_multiplier


class SpecCategory(BaseCatalogModel):
    """Категория характеристик"""

    name_ru = models.CharField(_("название (рус)"), max_length=255)
    name_en = models.CharField(_("название (англ)"), max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)

    class Meta:
        verbose_name = _("категория характеристик")
        verbose_name_plural = _("категории характеристик")
        ordering = ["sort_order", "name_ru"]

    def __str__(self):
        return self.name_ru


class Spec(BaseCatalogModel):
    """Характеристика товара"""

    name_ru = models.CharField(_("название (рус)"), max_length=255)
    name_en = models.CharField(_("название (англ)"), max_length=255, blank=True)
    category = models.ForeignKey(
        SpecCategory, on_delete=models.CASCADE, related_name="specs", verbose_name=_("категория")
    )
    value_ru = models.CharField(_("значение (рус)"), max_length=255)
    value_en = models.CharField(_("значение (англ)"), max_length=255, blank=True)
    price_modifier_rub = models.DecimalField(
        _("изменение цены (руб)"), max_digits=10, decimal_places=2, default=0
    )
    price_modifier_usd = models.DecimalField(
        _("изменение цены (USD)"), max_digits=10, decimal_places=2, default=0
    )
    image = models.ImageField(_("изображение"), upload_to="specs/", null=True, blank=True)
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="specs", verbose_name=_("товар")
    )
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)
    is_custom = models.BooleanField(
        _("кастомный вариант"),
        default=False,
        help_text=_("Цена рассчитывается менеджером индивидуально"),
    )

    class Meta:
        verbose_name = _("характеристика")
        verbose_name_plural = _("характеристики")
        ordering = ["sort_order", "name_ru"]

    def __str__(self):
        return f"{self.name_ru}: {self.value_ru}"


class SpecPhoto(BaseCatalogModel):
    """Фотография характеристики"""

    spec = models.ForeignKey(
        Spec, on_delete=models.CASCADE, related_name="photos", verbose_name=_("характеристика")
    )
    image = models.ImageField(_("изображение"), upload_to="spec_photos/")
    caption_ru = models.CharField(_("подпись (рус)"), max_length=255, blank=True)
    caption_en = models.CharField(_("подпись (англ)"), max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)

    class Meta:
        verbose_name = _("фото характеристики")
        verbose_name_plural = _("фото характеристик")
        ordering = ["sort_order"]

    def __str__(self):
        return f"Фото {self.spec.name_ru}: {self.spec.value_ru}"


class ItemPhoto(BaseCatalogModel):
    """Фотография товара"""

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="photo_objects", verbose_name=_("товар")
    )
    image = models.ImageField(_("изображение"), upload_to="items/photos/")
    caption_ru = models.CharField(_("подпись (рус)"), max_length=255, blank=True)
    caption_en = models.CharField(_("подпись (англ)"), max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)
    is_preview = models.BooleanField(_("превью"), default=False)

    class Meta:
        verbose_name = _("фотография")
        verbose_name_plural = _("фотографии")
        ordering = ["sort_order"]

    def __str__(self):
        return f"Фото {self.item.name_ru} - {self.sort_order}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_item_cache()

    def delete(self, *args, **kwargs):
        item = self.item
        super().delete(*args, **kwargs)
        self._update_item_cache(item)

    def _update_item_cache(self, item=None):
        if item is None:
            item = self.item
        all_photos = item.photo_objects.all().order_by("sort_order")
        preview_urls = [p.image.url for p in all_photos if p.is_preview]
        if not preview_urls and all_photos.exists():
            first_photo = all_photos.first()
            if first_photo:
                preview_urls = [first_photo.image.url]
        all_urls = [p.image.url for p in all_photos]
        Item.objects.filter(pk=item.pk).update(preview_photos=preview_urls, photos=all_urls)


class Service(BaseCatalogModel):
    """Модель Услуги"""

    name_ru = models.CharField(_("название (рус)"), max_length=500)
    name_en = models.CharField(_("название (англ)"), max_length=500, blank=True)
    description_ru = models.TextField(_("описание (рус)"), blank=True)
    description_en = models.TextField(_("описание (англ)"), blank=True)
    short_description_ru = models.TextField(_("Краткое описание (рус)"), blank=True)
    short_description_en = models.TextField(_("Краткое описание (англ)"), blank=True)
    preview_photos = models.JSONField(_("превью"), default=list, blank=True)
    photos = models.JSONField(_("фотографии"), default=list, blank=True)
    slug = models.SlugField(_("slug"), unique=True, max_length=255, db_index=True)
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)
    price_rub = models.DecimalField(
        _("цена (руб)"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_usd = models.DecimalField(
        _("цена (USD)"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_price_hidden = models.BooleanField(_("скрыть цену"), default=True)
    discounts = models.ManyToManyField(Discount, blank=True, related_name="services")
    is_active = models.BooleanField(_("активна"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Услуга")
        verbose_name_plural = _("Услуги")
        ordering = ["sort_order", "name_ru"]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            base_name = self.name_ru or self.name_en
            base = slugify(base_name)
            slug = base
            counter = 1
            while Service.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ServicePhoto(BaseCatalogModel):
    """Фотография услуги"""

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="photo_objects", verbose_name=_("услуга")
    )
    image = models.ImageField(_("изображение"), upload_to="services/photos/")
    caption_ru = models.CharField(_("подпись (рус)"), max_length=255, blank=True)
    caption_en = models.CharField(_("подпись (англ)"), max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(_("порядок"), default=0)
    is_preview = models.BooleanField(_("превью"), default=False)

    class Meta:
        verbose_name = _("фотография услуги")
        verbose_name_plural = _("фотографии услуг")
        ordering = ["sort_order"]

    def __str__(self):
        return f"Фото {self.service.name_ru} - {self.sort_order}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_service_cache()

    def delete(self, *args, **kwargs):
        service = self.service
        super().delete(*args, **kwargs)
        self._update_service_cache(service)

    def _update_service_cache(self, service=None):
        if service is None:
            service = self.service
        all_photos = service.photo_objects.all().order_by("sort_order")
        preview_urls = [p.image.url for p in all_photos if p.is_preview]
        if not preview_urls and all_photos.exists():
            first_photo = all_photos.first()
            if first_photo:
                preview_urls = [first_photo.image.url]
        all_urls = [p.image.url for p in all_photos]
        Service.objects.filter(pk=service.pk).update(preview_photos=preview_urls, photos=all_urls)
