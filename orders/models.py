from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import random

from users.models import User
from catalog.models import Item, Service


class OrderStatus(models.TextChoices):
    NEW = "new", _("Новый")
    CONFIRMED = "confirmed", _("Подтверждён")
    PAID = "paid", _("Оплачен")
    ASSEMBLING = "assembling", _("В сборке")
    SHIPPED = "shipped", _("Отправлен")
    DELIVERED = "delivered", _("Доставлен")
    CANCELLED = "cancelled", _("Отменён")


class PaymentStatus(models.TextChoices):
    PENDING = "pending", _("Ожидает")
    PAID = "paid", _("Оплачен")
    FAILED = "failed", _("Ошибка")
    REFUNDED = "refunded", _("Возврат")


class DeliveryAddress(models.Model):
    """Сохранённые адреса доставки пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="delivery_addresses",
        verbose_name=_("пользователь"),
    )
    label = models.CharField(
        _("метка"), max_length=50, blank=True, help_text=_("Дом, Работа, Дача")
    )
    address = models.TextField(_("адрес"))
    entrance = models.CharField(_("подъезд"), max_length=10, blank=True)
    floor = models.CharField(_("этаж"), max_length=10, blank=True)
    apartment = models.CharField(_("квартира/офис"), max_length=10, blank=True)
    comment = models.TextField(_("комментарий"), blank=True)
    has_elevator = models.BooleanField(_("есть лифт"), default=True)
    requires_assemblers = models.BooleanField(_("нужны сборщики"), default=False)
    is_default = models.BooleanField(_("адрес по умолчанию"), default=False)
    created_at = models.DateTimeField(_("создан"), auto_now_add=True)

    class Meta:
        verbose_name = _("адрес доставки")
        verbose_name_plural = _("адреса доставки")
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-is_default"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        default_mark = " ★" if self.is_default else ""
        return f"{self.address[:50]}{default_mark}"

    def full_address(self):
        parts = [self.address]
        if self.entrance:
            parts.append(f"подъезд {self.entrance}")
        if self.floor:
            parts.append(f"этаж {self.floor}")
        if self.apartment:
            parts.append(f"кв/офис {self.apartment}")
        if self.comment:
            parts.append(f"({self.comment})")
        return ", ".join(parts)


class PromoCode(models.Model):
    """Промокоды для скидок."""

    code = models.CharField(_("код"), max_length=50, unique=True, db_index=True)
    description = models.CharField(_("описание"), max_length=255, blank=True)
    discount_percent = models.PositiveIntegerField(_("скидка %"), default=0)
    discount_amount_rub = models.DecimalField(
        _("скидка ₽"), max_digits=10, decimal_places=2, default=0
    )
    discount_amount_usd = models.DecimalField(
        _("скидка $"), max_digits=10, decimal_places=2, default=0
    )
    valid_until = models.DateField(_("действует до"), null=True, blank=True)
    max_uses = models.PositiveIntegerField(_("макс. использований"), default=0)
    used_count = models.PositiveIntegerField(_("использовано"), default=0)
    is_active = models.BooleanField(_("активен"), default=True)

    class Meta:
        verbose_name = _("промокод")
        verbose_name_plural = _("промокоды")
        indexes = [
            models.Index(fields=["code", "is_active"]),
            models.Index(fields=["is_active", "valid_until"]),
        ]

    def __str__(self):
        if self.discount_percent:
            return f"{self.code} - {self.discount_percent}%"
        return f"{self.code} - {self.discount_amount_rub}₽"


class Order(models.Model):
    """Заказ пользователя."""

    order_number = models.CharField(_("номер заказа"), max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("пользователь"),
    )
    delivery_address = models.ForeignKey(
        DeliveryAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("адрес доставки"),
    )
    delivery_address_text = models.TextField(_("адрес (текст)"), blank=True)
    # Снимок данных на момент заказа
    email = models.EmailField(_("email"))
    phone = models.CharField(_("телефон"), max_length=20)
    full_name = models.CharField(_("полное имя"), max_length=255)
    delivery_instructions = models.TextField(_("инструкции для курьера"), blank=True)
    delivery_cost_rub = models.DecimalField(
        _("стоимость доставки (руб)"), max_digits=10, decimal_places=2, default=0
    )
    delivery_cost_usd = models.DecimalField(
        _("стоимость доставки (USD)"), max_digits=10, decimal_places=2, default=0
    )
    status = models.CharField(
        _("статус"),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        db_index=True,
    )
    payment_status = models.CharField(
        _("статус оплаты"),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    payment_method = models.CharField(_("способ оплаты"), max_length=50, blank=True)
    payment_id = models.CharField(_("ID платежа"), max_length=255, blank=True)
    paid_at = models.DateTimeField(_("оплачен"), null=True, blank=True)
    subtotal_rub = models.DecimalField(
        _("сумма товаров (руб)"), max_digits=10, decimal_places=2, default=0
    )
    subtotal_usd = models.DecimalField(
        _("сумма товаров (USD)"), max_digits=10, decimal_places=2, default=0
    )
    discount_rub = models.DecimalField(
        _("скидка (руб)"), max_digits=10, decimal_places=2, default=0
    )
    discount_usd = models.DecimalField(
        _("скидка (USD)"), max_digits=10, decimal_places=2, default=0
    )
    total_rub = models.DecimalField(_("итого (руб)"), max_digits=10, decimal_places=2, default=0)
    total_usd = models.DecimalField(_("итого (USD)"), max_digits=10, decimal_places=2, default=0)
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("промокод")
    )
    promo_code_text = models.CharField(_("промокод (текст)"), max_length=50, blank=True)
    promo_discount_rub = models.DecimalField(
        _("скидка промо (руб)"), max_digits=10, decimal_places=2, default=0
    )
    promo_discount_usd = models.DecimalField(
        _("скидка промо (USD)"), max_digits=10, decimal_places=2, default=0
    )
    customer_comment = models.TextField(_("комментарий клиента"), blank=True)
    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("заказ")
        verbose_name_plural = _("заказы")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"Заказ {self.order_number} - {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            date = timezone.now().strftime("%Y%m%d")
            random_num = random.randint(1000, 9999)
            self.order_number = f"ORD-{date}-{random_num}"
        if self.delivery_address and not self.delivery_address_text:
            self.delivery_address_text = self.delivery_address.full_address()
        if self.promo_code and not self.promo_code_text:
            self.promo_code_text = self.promo_code.code
        super().save(*args, **kwargs)

    def can_cancel(self):
        """Можно ли отменить заказ"""
        return self.status in [OrderStatus.NEW, OrderStatus.CONFIRMED]

    def can_refund(self):
        """Можно ли сделать возврат"""
        return self.status in [
            OrderStatus.PAID,
            OrderStatus.ASSEMBLING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ]


class OrderItem(models.Model):
    """Товар в заказе (снимок данных)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("заказ")
    )
    tracking_number = models.CharField(_("трек-номер"), max_length=100, blank=True)
    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("товар")
    )
    # Snapshot данных (чтобы заказ не ломался при изменении каталога)
    name = models.CharField(_("название"), max_length=500)
    sku = models.CharField(_("артикул"), max_length=100, blank=True)
    size_value_ru = models.CharField(_("размер"), max_length=100, blank=True)
    selected_spec_ids = models.JSONField(_("ID характеристик"), default=list, blank=True)
    selected_specs_snapshot = models.JSONField(_("Данные характеристик"), default=dict, blank=True)
    image = models.URLField(_("фото"), blank=True)
    quantity = models.PositiveIntegerField(_("количество"), default=1)
    price_rub = models.DecimalField(_("цена (руб)"), max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(_("цена (USD)"), max_digits=10, decimal_places=2, default=0)
    total_rub = models.DecimalField(_("итого (руб)"), max_digits=10, decimal_places=2)
    total_usd = models.DecimalField(_("итого (USD)"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("товар в заказе")
        verbose_name_plural = _("товары в заказе")
        indexes = [
            models.Index(fields=["order", "item"]),
            models.Index(fields=["item"]),
        ]

    def __str__(self):
        return f"{self.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.total_rub:
            self.total_rub = self.price_rub * self.quantity
        if not self.total_usd:
            self.total_usd = self.price_usd * self.quantity
        super().save(*args, **kwargs)


class OrderService(models.Model):
    """Услуга в заказе."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="services", verbose_name=_("заказ")
    )
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("услуга")
    )
    # Снимок на момент заказа
    name = models.CharField(_("название"), max_length=500)
    image = models.URLField(_("фото"), blank=True)
    quantity = models.PositiveIntegerField(_("количество"), default=1)
    price_rub = models.DecimalField(_("цена (руб)"), max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(_("цена (USD)"), max_digits=10, decimal_places=2, default=0)
    total_rub = models.DecimalField(_("итого (руб)"), max_digits=10, decimal_places=2)
    total_usd = models.DecimalField(_("итого (USD)"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("услуга в заказе")
        verbose_name_plural = _("услуги в заказе")

    def __str__(self):
        return f"{self.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.total_rub:
            self.total_rub = self.price_rub * self.quantity
        if not self.total_usd:
            self.total_usd = self.price_usd * self.quantity
        super().save(*args, **kwargs)
