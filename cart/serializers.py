from rest_framework import serializers
from catalog.models import Spec
from catalog.serializers import ItemListSerializer, SizeListSerializer, SpecListSerializer
from .models import Cart, CartItem


class CartItemCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления товара в корзину"""

    size_id = serializers.IntegerField(required=False, allow_null=True)
    spec_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])

    class Meta:
        model = CartItem
        fields = ["item", "size_id", "quantity", "spec_ids"]
        extra_kwargs = {
            "item": {"required": True},
            "quantity": {"default": 1, "min_value": 1},
        }

    def validate(self, attrs):
        item = attrs.get("item")
        if not item or not item.is_active:
            raise serializers.ValidationError({"item": "Товар не найден или не активен"})

        size_id = attrs.get("size_id")
        if size_id:
            try:
                size = item.sizes.get(id=size_id)
                if not size.is_available:
                    raise serializers.ValidationError({"size_id": "Размер недоступен"})
                attrs["size"] = size
            except item.sizes.model.DoesNotExist:
                raise serializers.ValidationError({"size_id": "Размер не найден для этого товара"})
        else:
            attrs["size"] = None

        spec_ids = attrs.get("spec_ids", [])
        if spec_ids:
            specs = Spec.objects.filter(id__in=spec_ids, item=item)
            if len(specs) != len(spec_ids):
                raise serializers.ValidationError(
                    {"spec_ids": "Некоторые характеристики не найдены"}
                )
            attrs["spec_ids"] = sorted([s.id for s in specs])
        else:
            attrs["spec_ids"] = []

        return attrs

    def create(self, validated_data):
        size = validated_data.pop("size", None)
        spec_ids = validated_data.pop("spec_ids", [])
        cart, _ = Cart.objects.get_or_create(user=self.context["request"].user)
        spec_ids = sorted(spec_ids)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            item=validated_data["item"],
            size=size,
            selected_spec_ids=spec_ids,
            defaults={
                "quantity": validated_data["quantity"],
            },
        )
        if not created:
            cart_item.quantity += validated_data["quantity"]
            cart_item.save()
        return cart_item


class CartItemDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор товара в корзине"""

    item = ItemListSerializer(read_only=True)
    size = SizeListSerializer(read_only=True)
    selected_specs = serializers.SerializerMethodField()
    price_rub = serializers.SerializerMethodField()
    price_usd = serializers.SerializerMethodField()
    subtotal_rub = serializers.SerializerMethodField()
    subtotal_usd = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "item",
            "size",
            "quantity",
            "selected_specs",
            "price_rub",
            "price_usd",
            "subtotal_rub",
            "subtotal_usd",
            "added_at",
        ]

    def get_selected_specs(self, obj):
        specs = Spec.objects.filter(id__in=obj.selected_spec_ids)
        return SpecListSerializer(specs, many=True).data

    def get_price_rub(self, obj):
        return obj.cached_price_rub

    def get_price_usd(self, obj):
        return obj.cached_price_usd

    def get_subtotal_rub(self, obj):
        return obj.cached_price_rub * obj.quantity

    def get_subtotal_usd(self, obj):
        return obj.cached_price_usd * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины"""

    items = CartItemDetailSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price_rub = serializers.SerializerMethodField()
    total_price_usd = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "total_items",
            "total_price_rub",
            "total_price_usd",
            "created_at",
            "updated_at",
        ]

    def get_total_items(self, obj):
        return obj.get_total_items()

    def get_total_price_rub(self, obj):
        return obj.get_total_price_rub()

    def get_total_price_usd(self, obj):
        total = 0
        for item in obj.items.all():
            total += item.cached_price_usd * item.quantity
        return round(total, 2)


class CartItemUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления количества"""

    class Meta:
        model = CartItem
        fields = ["quantity"]
        extra_kwargs = {"quantity": {"required": True, "min_value": 1}}
