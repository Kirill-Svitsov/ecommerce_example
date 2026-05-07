from rest_framework import serializers
from .models import Article, ArticleImage


class ArticleImageSerializer(serializers.ModelSerializer):
    """Сериализатор для изображений статьи"""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ArticleImage
        fields = ["id", "image", "image_url", "caption_ru", "caption_en", "sort_order", "article"]
        read_only_fields = ["id"]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class ArticleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка статей"""

    preview_photo_url = serializers.SerializerMethodField()
    preview_wide_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title_ru",
            "title_en",
            "short_description_ru",
            "short_description_en",
            "slug",
            "preview_photo",
            "preview_photo_url",
            "preview_wide_photo",
            "preview_wide_photo_url",
            "is_main",
            "sort_order",
            "published_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "sort_order"]

    def get_preview_photo_url(self, obj):
        if obj.preview_photo:
            return obj.preview_photo.url
        return None

    def get_preview_wide_photo_url(self, obj):
        if obj.preview_wide_photo:
            return obj.preview_wide_photo.url
        return None


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной страницы статьи"""

    photos = ArticleImageSerializer(many=True, read_only=True, source="images")
    preview_photo_url = serializers.SerializerMethodField()
    preview_wide_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title_ru",
            "title_en",
            "short_description_ru",
            "short_description_en",
            "description_ru",
            "description_en",
            "slug",
            "preview_photo",
            "preview_photo_url",
            "preview_wide_photo",
            "preview_wide_photo_url",
            "photos",
            "is_main",
            "sort_order",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "sort_order"]

    def get_preview_photo_url(self, obj):
        if obj.preview_photo:
            return obj.preview_photo.url
        return None

    def get_preview_wide_photo_url(self, obj):
        if obj.preview_wide_photo:
            return obj.preview_wide_photo.url
        return None


class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    upload_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text="Загрузите одно или несколько изображений",
    )
    photos = ArticleImageSerializer(many=True, read_only=True, source="images")

    class Meta:
        model = Article
        fields = [
            "id",
            "title_ru",
            "title_en",
            "short_description_ru",
            "short_description_en",
            "description_ru",
            "description_en",
            "slug",
            "preview_photo",
            "preview_wide_photo",
            "upload_images",
            "photos",
            "is_main",
            "is_published",
            "published_at",
            "sort_order",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "sort_order", "slug"]

    def create(self, validated_data):
        upload_images = validated_data.pop("upload_images", [])
        instance = Article.objects.create(**validated_data)
        for image in upload_images:
            ArticleImage.objects.create(article=instance, image=image)
        instance.refresh_from_db()
        return instance

    def update(self, instance, validated_data):
        upload_images = validated_data.pop("upload_images", [])
        instance = super().update(instance, validated_data)
        for image in upload_images:
            ArticleImage.objects.create(article=instance, image=image)
        instance.refresh_from_db()
        return instance


class ArticleAdminSerializer(serializers.ModelSerializer):
    """Сериализатор для админской панели (полный контроль)"""

    photos = ArticleImageSerializer(many=True, read_only=True)
    photos_ids = serializers.PrimaryKeyRelatedField(
        source="photos",
        many=True,
        queryset=ArticleImage.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Article
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
