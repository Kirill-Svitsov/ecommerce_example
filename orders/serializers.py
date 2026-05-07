from django.utils import timezone
from django.db.models import Sum
from rest_framework import serializers
from .models import Order, OrderItem, OrderService, DeliveryAddress, PromoCode
from catalog.serializers import ItemListSerializer


class DeliveryAddressSerializer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryAddress
        fields = [
            "id",
            "label",
            "address",
            "entrance",
            "floor",
            "apartment",
            "comment",
            "has_elevator",
            "requires_assemblers",
            "is_default",
            "full_address",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_full_address(self, obj):
        return obj.full_address()

    def create(self, validated_data):
        if validated_data.get("is_default"):
            DeliveryAddress.objects.filter(user=validated_data["user"], is_default=True).update(
                is_default=False
            )
        return super().create(validated_data)


class DeliveryAddressAdminSerializer(DeliveryAddressSerializer):
    """Сериализатор для админов (с информацией о пользователе)"""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta(DeliveryAddressSerializer.Meta):
        fields = DeliveryAddressSerializer.Meta.fields + ["user_id", "user_email", "user_name"]


class DeliveryAddressBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = ["id", "label", "address", "is_default"]


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = [
            "code",
            "description",
            "discount_percent",
            "discount_amount_rub",
            "discount_amount_usd",
            "valid_until",
            "max_uses",
            "used_count",
            "is_active",
        ]


class PromoCodeValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)

    def validate_code(self, value):
        try:
            promo = PromoCode.objects.get(code=value, is_active=True)
            if promo.valid_until and promo.valid_until < timezone.now().date():
                raise serializers.ValidationError("Промокод истёк")
            if promo.max_uses and promo.used_count >= promo.max_uses:
                raise serializers.ValidationError("Промокод больше не действует")
            return value
        except PromoCode.DoesNotExist:
            raise serializers.ValidationError("Промокод не найден")


class OrderItemSerializer(serializers.ModelSerializer):
    item = ItemListSerializer(read_only=True)
    specs_snapshot = serializers.JSONField(source="selected_specs_snapshot", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item",
            "name",
            "sku",
            "size_value_ru",
            "quantity",
            "price_rub",
            "price_usd",
            "total_rub",
            "total_usd",
            "specs_snapshot",
            "image",
        ]


class OrderItemCreateSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    size_id = serializers.IntegerField(required=False, allow_null=True)
    spec_ids = serializers.ListField(child=serializers.IntegerField(), default=list)
    quantity = serializers.IntegerField(min_value=1, default=1)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    services = serializers.SerializerMethodField()
    delivery_address_info = DeliveryAddressBriefSerializer(
        source="delivery_address", read_only=True
    )
    can_cancel = serializers.ReadOnlyField()
    can_refund = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "status",
            "payment_status",
            "payment_method",
            "delivery_address_info",
            "delivery_cost_rub",
            "delivery_cost_usd",
            "subtotal_rub",
            "subtotal_usd",
            "discount_rub",
            "discount_usd",
            "total_rub",
            "total_usd",
            "promo_code_text",
            "customer_comment",
            "items",
            "services",
            "can_cancel",
            "can_refund",
            "created_at",
            "paid_at",
        ]
        read_only_fields = [
            "order_number",
            "status",
            "payment_status",
            "total_rub",
            "total_usd",
            "created_at",
            "paid_at",
        ]

    def get_services(self, obj):
        return OrderServiceSerializer(obj.services.all(), many=True).data


class OrderCreateSerializer(serializers.Serializer):
    """Сериализатор для создания заказа"""

    # Адрес
    delivery_address_id = serializers.IntegerField(required=False, allow_null=True)
    delivery_address_text = serializers.CharField(required=False, allow_blank=True)
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
    delivery_cost_rub = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_cost_usd = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Контакты
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    full_name = serializers.CharField(max_length=255)

    # Оплата
    payment_method = serializers.CharField(max_length=50, default="card")

    # Промокод
    promo_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    # Комментарии
    customer_comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get("delivery_address_id") and not data.get("delivery_address_text"):
            raise serializers.ValidationError(
                {"address": "Укажите адрес доставки или выберите сохранённый"}
            )

        if data.get("promo_code"):
            try:
                promo = PromoCode.objects.get(code=data["promo_code"], is_active=True)
                if promo.valid_until and promo.valid_until < timezone.now().date():
                    raise serializers.ValidationError({"promo_code": "Промокод истёк"})
            except PromoCode.DoesNotExist:
                raise serializers.ValidationError({"promo_code": "Промокод не найден"})

        return data


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "payment_status",
            "total_rub",
            "total_usd",
            "items_count",
            "created_at",
        ]

    def get_items_count(self, obj):
        return obj.items.aggregate(total=Sum("quantity"))["total"] or 0


class OrderServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderService
        fields = [
            "id",
            "name",
            "quantity",
            "price_rub",
            "price_usd",
            "total_rub",
            "total_usd",
        ]
