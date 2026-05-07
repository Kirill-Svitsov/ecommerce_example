from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Category,
    Author,
    Item,
    Size,
    Spec,
    SpecCategory,
    ItemPhoto,
    Service,
    Discount,
    SpecPhoto,
    ServicePhoto,
)


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = [
            "id",
            "name_ru",
            "name_en",
            "value",
            "type",
            "valid_from",
            "valid_to",
            "is_active",
        ]


class CategoryListSerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name_ru",
            "name_en",
            "slug",
            "parent",
            "sort_order",
            "is_active",
            "children_count",
            "items_count",
        ]

    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count()

    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    discounts = DiscountSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name_ru",
            "name_en",
            "description_ru",
            "description_en",
            "slug",
            "parent",
            "sort_order",
            "is_active",
            "children",
            "items_count",
            "discounts",
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by("sort_order")
        return CategoryListSerializer(children, many=True, context=self.context).data

    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "name_ru",
            "name_en",
            "description_ru",
            "description_en",
            "slug",
            "parent",
            "sort_order",
            "is_active",
        ]

    def validate_parent(self, value):
        """
        Запрещаем создавать категории без родителя через API
        """
        if not self.instance and not value:
            raise serializers.ValidationError(
                _(
                    "Категория должна иметь родителя. "
                    "Корневые категории создаются только через админку."
                )
            )
        if self.instance and self.instance.parent and not value:
            raise serializers.ValidationError(
                _("Нельзя сделать категорию корневой через API. Используйте админку.")
            )
        if value and self.instance and value.id == self.instance.id:
            raise serializers.ValidationError(_("Категория не может быть родителем самой себя"))
        return value


class AuthorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name_ru", "name_en", "slug", "photo"]


class AuthorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name_ru", "name_en", "bio_ru", "bio_en", "slug", "photo"]


class AuthorCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name_ru", "name_en", "bio_ru", "bio_en", "slug", "photo"]


class SpecCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecCategory
        fields = ["id", "name_ru", "name_en", "sort_order"]


class SpecCategoryDetailSerializer(serializers.ModelSerializer):
    specs_count = serializers.SerializerMethodField()

    class Meta:
        model = SpecCategory
        fields = ["id", "name_ru", "name_en", "sort_order", "specs_count"]

    def get_specs_count(self, obj):
        return obj.specs.count()


class SpecCategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecCategory
        fields = ["name_ru", "name_en", "sort_order"]


class SpecPhotoSerializer(serializers.ModelSerializer):
    spec = serializers.PrimaryKeyRelatedField(
        queryset=Spec.objects.all(), write_only=True, required=True
    )

    class Meta:
        model = SpecPhoto
        fields = ["id", "spec", "image", "caption_ru", "caption_en", "sort_order"]
        read_only_fields = ["id"]


class SpecListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name_ru", read_only=True)
    photos = SpecPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Spec
        fields = [
            "id",
            "name_ru",
            "name_en",
            "category_name",
            "is_custom",
            "value_ru",
            "value_en",
            "price_modifier_rub",
            "sort_order",
            "image",
            "photos",
        ]


class SpecDetailSerializer(serializers.ModelSerializer):
    category = SpecCategoryListSerializer(read_only=True)
    item_name = serializers.CharField(source="item.name_ru", read_only=True)
    photos = SpecPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Spec
        fields = [
            "id",
            "name_ru",
            "name_en",
            "category",
            "item_name",
            "value_ru",
            "value_en",
            "price_modifier_rub",
            "price_modifier_usd",
            "image",
            "sort_order",
            "is_custom",
            "photos",
        ]


class SpecCreateUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=True)
    price_modifier_rub = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    price_modifier_usd = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Spec
        fields = [
            "name_ru",
            "name_en",
            "category_id",
            "item",
            "value_ru",
            "value_en",
            "price_modifier_rub",
            "price_modifier_usd",
            "image",
            "sort_order",
            "is_custom",
        ]


class SizeListSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()

    class Meta:
        model = Size
        fields = [
            "id",
            "value_ru",
            "value_en",
            "price_multiplier",
            "is_available",
            "is_custom",
            "price_display",
        ]

    @staticmethod
    def get_price_display(obj):
        if obj.is_custom:
            return "Индивидуальный расчет"
        if obj.override_price_rub:
            return f"{obj.override_price_rub} ₽"
        if obj.price_multiplier != 1.0:
            return f"×{obj.price_multiplier} от базовой"
        return "Базовая цена"


class SizeDetailSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name_ru", read_only=True)

    class Meta:
        model = Size
        fields = [
            "id",
            "value_ru",
            "value_en",
            "price_multiplier",
            "override_price_rub",
            "override_price_usd",
            "is_available",
            "sort_order",
            "item_name",
            "is_custom",
        ]


class SizeCreateUpdateSerializer(serializers.ModelSerializer):
    price_multiplier = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    override_price_rub = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    override_price_usd = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    is_custom = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Size
        fields = [
            "value_ru",
            "value_en",
            "price_multiplier",
            "override_price_rub",
            "override_price_usd",
            "item",
            "is_available",
            "sort_order",
            "is_custom",
        ]

    def validate(self, data):
        """
        Валидация: если is_custom=True, то price_multiplier и override_price не обязательны
        """
        if data.get("is_custom"):
            data["price_multiplier"] = 1.0
            data["override_price_rub"] = None
            data["override_price_usd"] = None
        return data


class ItemListSerializer(serializers.ModelSerializer):
    category_name_ru = serializers.CharField(source="category.name_ru", read_only=True)
    category_name_en = serializers.CharField(source="category.name_en", read_only=True)
    author_name = serializers.CharField(source="author.name_ru", read_only=True)
    discount = serializers.SerializerMethodField()
    final_price_rub = serializers.SerializerMethodField()
    final_price_usd = serializers.SerializerMethodField()
    favourite_id = serializers.SerializerMethodField()  # 👈 ДОБАВИТЬ

    class Meta:
        model = Item
        fields = [
            "id",
            "name_ru",
            "name_en",
            "slug",
            "category_name_ru",
            "category_name_en",
            "author_name",
            "base_price_rub",
            "base_price_usd",
            "is_price_hidden",
            "preview_photos",
            "is_art",
            "art_description_ru",
            "art_description_en",
            "art_size",
            "discount",
            "final_price_rub",
            "final_price_usd",
            "is_active",
            "created_at",
            "availability",
            "lead_time_days",
            "creation_year",
            "weight",
            "material",
            "technique",
            "favourite_id",
        ]

    def get_discount(self, obj):
        discount = obj.get_active_discount()
        return DiscountSerializer(discount).data if discount else None

    def get_final_price_rub(self, obj):
        return obj.calculate_price(currency="rub")

    def get_final_price_usd(self, obj):
        return obj.calculate_price(currency="usd")

    def get_favourite_id(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            favourite = obj.favourited_by.filter(user=request.user).first()
            return favourite.id if favourite else None
        return None


class ItemDetailSerializer(serializers.ModelSerializer):
    category_name_ru = serializers.CharField(source="category.name_ru", read_only=True)
    category_name_en = serializers.CharField(source="category.name_en", read_only=True)
    category_id = serializers.IntegerField(source="category.id", read_only=True)
    author = AuthorListSerializer(read_only=True)
    sizes = serializers.SerializerMethodField()
    specs_by_category = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    final_price_rub = serializers.SerializerMethodField()
    final_price_usd = serializers.SerializerMethodField()
    favourite_id = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            "id",
            "name_ru",
            "name_en",
            "description_ru",
            "description_en",
            "category_id",
            "slug",
            "category_name_ru",
            "category_name_en",
            "author",
            "is_art",
            "art_description_ru",
            "art_description_en",
            "is_active",
            "base_price_rub",
            "base_price_usd",
            "is_price_hidden",
            "image_2d",
            "image_3d",
            "preview_photos",
            "photos",
            "sizes",
            "specs_by_category",
            "discount",
            "final_price_rub",
            "final_price_usd",
            "created_at",
            "updated_at",
            "availability",
            "lead_time_days",
            "creation_year",
            "art_size",
            "weight",
            "material",
            "technique",
            "favourite_id",
        ]

    def get_specs_by_category(self, obj):
        specs = (
            obj.specs.all()
            .select_related("category")
            .prefetch_related("photos")
            .order_by("category__sort_order", "sort_order")
        )
        grouped = {}
        for spec in specs:
            cat_id = spec.category.id
            if cat_id not in grouped:
                grouped[cat_id] = {
                    "category": {
                        "id": spec.category.id,
                        "name_ru": spec.category.name_ru,
                        "name_en": spec.category.name_en,
                    },
                    "specs": [],
                }
            spec_data = {
                "id": spec.id,
                "name_ru": spec.name_ru,
                "name_en": spec.name_en,
                "value_ru": spec.value_ru,
                "value_en": spec.value_en,
                "price_modifier_rub": spec.price_modifier_rub if not spec.is_custom else 0,
                "price_modifier_usd": spec.price_modifier_usd if not spec.is_custom else 0,
                "image": spec.image.url if spec.image else None,
                "is_custom": spec.is_custom,
                "price_display": "Индивидуальный расчет" if spec.is_custom else None,
                "photos": [
                    {
                        "id": p.id,
                        "image": p.image.url,
                        "caption_ru": p.caption_ru,
                        "caption_en": p.caption_en,
                        "sort_order": p.sort_order,
                    }
                    for p in spec.photos.all().order_by("sort_order")
                ],
            }
            grouped[cat_id]["specs"].append(spec_data)
        return list(grouped.values())

    def get_discount(self, obj):
        discount = obj.get_active_discount()
        return DiscountSerializer(discount).data if discount else None

    def get_final_price_rub(self, obj):
        return obj.calculate_price(currency="rub")

    def get_final_price_usd(self, obj):
        return obj.calculate_price(currency="usd")

    def get_sizes(self, obj):
        sizes = obj.sizes.all().order_by("sort_order")
        return [
            {
                "id": size.id,
                "value_ru": size.value_ru,
                "value_en": size.value_en,
                "price_multiplier": size.price_multiplier,
                "override_price_rub": size.override_price_rub,
                "override_price_usd": size.override_price_usd,
                "is_available": size.is_available,
                "is_custom": size.is_custom,
                "price_display": "Индивидуальный расчет" if size.is_custom else None,
                "final_price_rub": size.get_price_rub() if not size.is_custom else None,
                "final_price_usd": size.get_price_usd() if not size.is_custom else None,
            }
            for size in sizes
        ]

    def get_favourite_id(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            favourite = obj.favourited_by.filter(user=request.user).first()
            return favourite.id if favourite else None
        return None


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=True)
    author_id = serializers.IntegerField(required=False, allow_null=True)
    base_price_rub = serializers.DecimalField(max_digits=10, decimal_places=2)
    base_price_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    art_description_ru = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    art_description_en = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Item
        fields = [
            "name_ru",
            "name_en",
            "description_ru",
            "description_en",
            "is_art",
            "art_description_ru",
            "art_description_en",
            "art_size",
            "slug",
            "category_id",
            "author_id",
            "base_price_rub",
            "base_price_usd",
            "is_price_hidden",
            "image_2d",
            "image_3d",
            "is_active",
            "sort_order",
            "availability",
            "lead_time_days",
            "creation_year",
            "weight",
            "material",
            "technique",
        ]

    def validate(self, data):
        """
        Валидация: если is_art=True, то art_description_ru обязателен
        """
        if data.get("is_art"):
            art_desc_ru = data.get("art_description_ru")
            if not art_desc_ru:
                raise serializers.ValidationError(
                    {
                        "art_description_ru": _(
                            "Для АРТа необходимо указать описание на русском языке"
                        )
                    }
                )
        return data


class ServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name_ru",
            "name_en",
            "slug",
            "short_description_ru",
            "short_description_en",
            "preview_photos",
            "price_rub",
            "price_usd",
            "is_price_hidden",
            "is_active",
            "created_at",
        ]


class ServiceDetailSerializer(serializers.ModelSerializer):
    discounts = DiscountSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "name_ru",
            "name_en",
            "description_ru",
            "description_en",
            "short_description_ru",
            "short_description_en",
            "slug",
            "preview_photos",
            "sort_order",
            "price_rub",
            "price_usd",
            "is_price_hidden",
            "discounts",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    price_rub = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    price_usd = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        model = Service
        fields = [
            "name_ru",
            "name_en",
            "description_ru",
            "description_en",
            "short_description_ru",
            "short_description_en",
            "slug",
            "sort_order",
            "price_rub",
            "price_usd",
            "is_price_hidden",
            "discounts",
            "is_active",
        ]


class DiscountListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ["id", "name_ru", "value", "type", "is_active"]


class ItemPhotoSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = ItemPhoto
        fields = ["id", "item_id", "image", "caption_ru", "caption_en", "sort_order", "is_preview"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        item_id = validated_data.pop("item_id")
        item = Item.objects.get(id=item_id)
        return ItemPhoto.objects.create(item=item, **validated_data)


class ServicePhotoSerializer(serializers.ModelSerializer):
    service_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = ServicePhoto
        fields = [
            "id",
            "service_id",
            "image",
            "caption_ru",
            "caption_en",
            "sort_order",
            "is_preview",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        service_id = validated_data.pop("service_id")
        service = Service.objects.get(id=service_id)
        return ServicePhoto.objects.create(service=service, **validated_data)


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name_ru", "name_en", "slug", "children", "items_count", "is_active"]

    def get_children(self, obj):
        # Получаем флаг из контекста
        include_inactive = self.context.get("include_inactive", False)
        # Фильтруем дочерние категории
        children_qs = obj.children.all().order_by("sort_order")
        if not include_inactive:
            children_qs = children_qs.filter(is_active=True)
        return CategoryTreeSerializer(children_qs, many=True, context=self.context).data

    def get_items_count(self, obj):
        # Подсчет активных товаров (или всех, если include_inactive)
        include_inactive = self.context.get("include_inactive", False)
        if include_inactive:
            return obj.items.count()
        return obj.items.filter(is_active=True).count()


class DiscountCreateUpdateSerializer(serializers.ModelSerializer):
    """Для создания и обновления скидок"""

    class Meta:
        model = Discount
        fields = "__all__"


class DiscountDetailSerializer(serializers.ModelSerializer):
    """Для детального просмотра скидки"""

    categories = CategoryListSerializer(many=True, read_only=True)
    items = ItemListSerializer(many=True, read_only=True)

    class Meta:
        model = Discount
        fields = "__all__"
