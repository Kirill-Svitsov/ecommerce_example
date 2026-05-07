from django.db import models
from rest_framework import serializers
from catalog.serializers import ItemListSerializer
from .models import Favourite


class FavouriteSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного (чтение)"""

    item = ItemListSerializer(read_only=True)

    class Meta:
        model = Favourite
        fields = ["id", "item", "position", "on_moodboard", "moodboard_position", "created_at"]


class FavouriteCreateSerializer(serializers.ModelSerializer):
    """Создание записи в избранном"""

    class Meta:
        model = Favourite
        fields = ["item"]
        extra_kwargs = {"item": {"required": True}}

    def validate(self, attrs):
        user = self.context["request"].user
        item = attrs.get("item")

        if Favourite.objects.filter(user=user, item=item).exists():
            raise serializers.ValidationError({"item": "Этот товар уже в избранном"})
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        max_position = (
            Favourite.objects.filter(user=user).aggregate(max=models.Max("position"))["max"] or -1
        )

        validated_data["user"] = user
        validated_data["position"] = max_position + 1
        validated_data["moodboard_position"] = max_position + 1
        return super().create(validated_data)


class FavouriteToggleMoodboardSerializer(serializers.ModelSerializer):
    """Переключение видимости в Moodboard"""

    class Meta:
        model = Favourite
        fields = ["on_moodboard"]
        extra_kwargs = {"on_moodboard": {"required": True}}


class FavouriteBulkReorderSerializer(serializers.Serializer):
    """
    Массовое обновление порядка.
    Применяется и для общего списка, и для Moodboard.
    """

    type = serializers.ChoiceField(choices=["all", "moodboard"], required=True)
    order = serializers.ListField(child=serializers.IntegerField(), required=True)

    def validate_order(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("Список ID не может быть пустым")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        item_ids = attrs["order"]
        order_type = attrs["type"]

        if order_type == "all":
            existing_count = Favourite.objects.filter(user=user).count()
        else:
            existing_count = Favourite.objects.filter(user=user, on_moodboard=True).count()

        if len(item_ids) != existing_count:
            raise serializers.ValidationError(
                f"Количество ID ({len(item_ids)}) не совпадает "
                f"с количеством товаров в избранном ({existing_count})"
            )

        user_item_ids = set(Favourite.objects.filter(user=user).values_list("item_id", flat=True))

        if not set(item_ids).issubset(user_item_ids):
            raise serializers.ValidationError("Некоторые товары не принадлежат пользователю")

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        order_type = self.validated_data["type"]
        item_ids = self.validated_data["order"]

        favourites = Favourite.objects.filter(user=user)

        if order_type == "all":
            for idx, item_id in enumerate(item_ids):
                favourites.filter(item_id=item_id).update(position=idx)
        else:
            for idx, item_id in enumerate(item_ids):
                favourites.filter(item_id=item_id, on_moodboard=True).update(moodboard_position=idx)
        return favourites.first()

    class Meta:
        swagger_schema_fields = {"example": {"type": "all", "order": [5, 2, 8, 1, 3]}}


class FavouriteRemoveFromMoodboardSerializer(serializers.ModelSerializer):
    """Удаление из Moodboard (просто переключает флаг)"""

    class Meta:
        model = Favourite
        fields = []

    def update(self, instance, validated_data):
        instance.on_moodboard = False
        instance.save()
        return instance
