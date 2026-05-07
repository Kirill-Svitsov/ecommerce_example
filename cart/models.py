from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from catalog.models import Item, Size, Spec
from users.models import User


class Cart(models.Model):
    """Корзина пользователя"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="cart", verbose_name=_("пользователь")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("корзина")
        verbose_name_plural = _("корзины")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Корзина {self.user.email}"

    def get_total_items(self):
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    def get_total_price_rub(self):
        total = 0
        for item in self.items.all():
            total += item.cached_price_rub * item.quantity
        return round(total, 2)

    def get_total_price_usd(self):
        total = 0
        for item in self.items.all():
            total += item.cached_price_usd * item.quantity
        return round(total, 2)


class CartItem(models.Model):
    """Товар в корзине"""

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items", verbose_name=_("корзина")
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="cart_items", verbose_name=_("товар")
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("размер"),
    )
    quantity = models.PositiveIntegerField(
        _("количество"), default=1, validators=[MinValueValidator(1)]
    )
    selected_spec_ids = models.JSONField(_("выбранные характеристики"), default=list, blank=True)
    spec_hash = models.CharField(max_length=64, editable=False, blank=True, db_index=True)
    # Кэш цены (чтобы не делать запросы при каждом обращении)
    cached_price_rub = models.DecimalField(
        _("кэш цены (руб)"), max_digits=10, decimal_places=2, default=0, editable=False
    )
    cached_price_usd = models.DecimalField(
        _("кэш цены (USD)"), max_digits=10, decimal_places=2, default=0, editable=False
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_("добавлен"))

    class Meta:
        verbose_name = _("товар в корзине")
        verbose_name_plural = _("товары в корзине")
        ordering = ["-added_at"]
        unique_together = ["cart", "item", "size", "spec_hash"]
        indexes = [
            models.Index(fields=["cart", "added_at"]),
            models.Index(fields=["item"]),
        ]

    def __str__(self):
        specs_str = ", ".join(str(sid) for sid in self.selected_spec_ids)
        size_str = f" - {self.size.value_ru}" if self.size else ""
        return f"{self.item.name_ru}{size_str} [{specs_str}] x{self.quantity}"

    def save(self, *args, **kwargs):
        # Генерируем хеш из отсортированных ID характеристик
        if self.selected_spec_ids:
            import hashlib

            sorted_ids = sorted(self.selected_spec_ids)
            self.spec_hash = hashlib.md5(str(sorted_ids).encode()).hexdigest()

        # Кэшируем цену (только если товар уже привязан)
        if self.item_id:
            specs = Spec.objects.filter(id__in=self.selected_spec_ids)
            self.cached_price_rub = self.item.calculate_price(
                size=self.size, selected_specs=specs, currency="rub"
            )
            self.cached_price_usd = self.item.calculate_price(
                size=self.size, selected_specs=specs, currency="usd"
            )

        super().save(*args, **kwargs)

    def get_price_rub(self):
        return self.cached_price_rub

    def get_price_usd(self):
        return self.cached_price_usd

    def get_subtotal_rub(self):
        return round(self.cached_price_rub * self.quantity, 2)

    def get_subtotal_usd(self):
        return round(self.cached_price_usd * self.quantity, 2)
