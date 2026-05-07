from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Category,
    Author,
    Item,
    Service,
    Discount,
    Spec,
    SpecCategory,
    Size,
    ItemPhoto,
    SpecPhoto,
    ServicePhoto,
)
from .serializers import (
    CategoryListSerializer,
    CategoryDetailSerializer,
    AuthorListSerializer,
    AuthorDetailSerializer,
    SpecCategoryListSerializer,
    SpecCategoryDetailSerializer,
    SpecListSerializer,
    SpecDetailSerializer,
    SizeListSerializer,
    SizeDetailSerializer,
    ItemListSerializer,
    ItemDetailSerializer,
    ServiceListSerializer,
    ServiceDetailSerializer,
    DiscountListSerializer,
    CategoryTreeSerializer,
    CategoryCreateUpdateSerializer,
    AuthorCreateUpdateSerializer,
    ItemCreateUpdateSerializer,
    ServiceCreateUpdateSerializer,
    SpecCategoryCreateUpdateSerializer,
    SpecCreateUpdateSerializer,
    SizeCreateUpdateSerializer,
    DiscountCreateUpdateSerializer,
    DiscountDetailSerializer,
    SpecPhotoSerializer,
    ItemPhotoSerializer,
    ServicePhotoSerializer,
)


class BaseCatalogViewSet(viewsets.ModelViewSet):
    """Базовый класс для вьюсетов каталога"""

    def get_permissions(self):
        """
        Права доступа:
        - Для небезопасных методов (POST, PUT, PATCH, DELETE) - только админ
        - Для безопасных методов (GET, HEAD, OPTIONS) - все
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class CategoryViewSet(BaseCatalogViewSet):
    queryset = Category.objects.all()
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name_ru", "name_en"]

    def get_queryset(self):
        if self.action == "list":
            # Проверяем параметр include_inactive
            include_inactive = (
                self.request.query_params.get("include_inactive", "false").lower() == "true"
            )

            # Базовый фильтр для корневых категорий
            queryset = Category.objects.filter(parent__isnull=True)

            # Если не включаем неактивные
            if not include_inactive:
                queryset = queryset.filter(is_active=True)

            return queryset
        return Category.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return CategoryListSerializer
        elif self.action == "retrieve":
            return CategoryDetailSerializer
        return CategoryCreateUpdateSerializer

    @swagger_auto_schema(
        method="get",
        operation_description="Дерево категорий. Параметры: "
        "include_inactive: если true, включает неактивные категории (только для админов)",
        manual_parameters=[
            openapi.Parameter(
                "include_inactive",
                openapi.IN_QUERY,
                description="Включать неактивные категории (только для админов)",
                type=openapi.TYPE_BOOLEAN,
                default=False,
            ),
        ],
        responses={
            200: CategoryTreeSerializer(many=True),
            403: "Доступ запрещен (при include_inactive=true без прав админа)",
        },
    )
    @action(detail=False, methods=["get"])
    def tree(self, request):
        """Дерево категорий.
        Параметры:
        - include_inactive: если true, включает неактивные категории (только для админов)
        """
        # Проверяем параметр include_inactive
        include_inactive = request.query_params.get("include_inactive", "false").lower() == "true"
        # Для неактивных нужны права админа
        if include_inactive and not request.user.is_staff:
            return Response({"error": "Доступ запрещен. Только для администраторов."}, status=403)
        # Базовый фильтр
        filter_kwargs = {"parent__isnull": True}
        if not include_inactive:
            filter_kwargs["is_active"] = True
        categories = Category.objects.filter(**filter_kwargs).order_by("sort_order")
        # Создаем сериализатор с контекстом для вложенных категорий
        context = {"request": request, "include_inactive": include_inactive}
        serializer = CategoryTreeSerializer(categories, many=True, context=context)
        return Response(serializer.data)


class AuthorViewSet(BaseCatalogViewSet):
    queryset = Author.objects.all()
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name_ru", "name_en"]

    def get_serializer_class(self):
        if self.action == "list":
            return AuthorListSerializer
        elif self.action == "retrieve":
            return AuthorDetailSerializer
        return AuthorCreateUpdateSerializer


class ItemViewSet(BaseCatalogViewSet):
    queryset = Item.objects.all()
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "author", "is_art", "is_active"]
    search_fields = ["name_ru", "name_en", "description_ru", "description_en"]
    ordering_fields = ["created_at", "sort_order", "base_price_rub"]
    ordering = ["sort_order"]

    def get_queryset(self):
        queryset = Item.objects.all()

        # Получаем значение фильтра is_active из запроса
        is_active_filter = self.request.query_params.get("is_active", None)

        # Если пользователь НЕ админ
        if not self.request.user.is_staff:
            # Всегда показываем только активные, игнорируя фильтр
            queryset = queryset.filter(is_active=True)
        else:
            # Если админ и фильтр is_active=false - показываем только неактивные
            if is_active_filter == "false":
                queryset = queryset.filter(is_active=False)
            # Если админ и фильтр is_active=true - показываем только активные
            elif is_active_filter == "true":
                queryset = queryset.filter(is_active=True)
            # Если админ и нет фильтра - показываем все
            # else: queryset остается без фильтрации по is_active

        # Оптимизация запросов
        queryset = queryset.prefetch_related(
            "category",
            "author",
            "sizes",
            "specs",
            "specs__category",
            "discounts",
            "category__discounts",
            "photo_objects",
        )

        # Фильтр по категории
        category_slug = self.request.query_params.get("category_slug")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ItemListSerializer
        elif self.action == "retrieve":
            return ItemDetailSerializer
        return ItemCreateUpdateSerializer


class ServiceViewSet(BaseCatalogViewSet):
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name_ru", "name_en", "description_ru", "description_en"]
    ordering_fields = ["created_at", "sort_order"]
    ordering = ["sort_order"]

    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        if self.request.user.is_staff and self.action == "list":
            queryset = Service.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ServiceListSerializer
        elif self.action == "retrieve":
            return ServiceDetailSerializer
        return ServiceCreateUpdateSerializer


class SpecCategoryViewSet(BaseCatalogViewSet):
    queryset = SpecCategory.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return SpecCategoryListSerializer
        elif self.action == "retrieve":
            return SpecCategoryDetailSerializer
        return SpecCategoryCreateUpdateSerializer


class SpecViewSet(BaseCatalogViewSet):
    queryset = Spec.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category", "item"]

    def get_serializer_class(self):
        if self.action == "list":
            return SpecListSerializer
        elif self.action == "retrieve":
            return SpecDetailSerializer
        return SpecCreateUpdateSerializer


class SizeViewSet(BaseCatalogViewSet):
    queryset = Size.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item"]

    def get_serializer_class(self):
        if self.action == "list":
            return SizeListSerializer
        elif self.action == "retrieve":
            return SizeDetailSerializer
        return SizeCreateUpdateSerializer


class DiscountViewSet(BaseCatalogViewSet):
    """
    Вьюсет для скидок.
    - В публичном API: только активные скидки
    - В админском API: все скидки через BaseCatalogViewSet
    """

    queryset = Discount.objects.all()
    serializer_class = DiscountListSerializer

    def get_queryset(self):
        """
        Для публичного API - только активные скидки
        Для админского API - все скидки (через BaseCatalogViewSet)
        """
        queryset = super().get_queryset()

        # Если запрос через публичное API (определяем по middleware или пути)
        if not self.request.path.startswith("/admin-api/"):
            return queryset.filter(is_active=True)

        # Для админского API - все скидки
        return queryset

    def get_serializer_class(self):
        """
        Разные сериализаторы для разных действий
        """
        if self.action in ["create", "update", "partial_update"]:
            return DiscountCreateUpdateSerializer
        elif self.action == "retrieve":
            return DiscountDetailSerializer
        return DiscountListSerializer


class GlobalSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Глобальный поиск по всем "
        "сущностям каталога (товары, АРТы, категории, авторы, услуги)",
        manual_parameters=[
            openapi.Parameter(
                "q",
                openapi.IN_QUERY,
                description="Поисковый запрос (минимум 2 символа)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Результаты поиска",
                examples={
                    "application/json": {
                        "items": [],
                        "artworks": [],
                        "categories": [],
                        "authors": [],
                        "services": [],
                    }
                },
            ),
            400: openapi.Response(description="Запрос слишком короткий"),
        },
    )
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response(
                {
                    "items": [],
                    "categories": [],
                    "authors": [],
                    "services": [],
                    "artworks": [],
                }
            )

        results = {
            "items": [],
            "categories": [],
            "authors": [],
            "services": [],
            "artworks": [],
        }

        # Поиск товаров (включая АРТы)
        items_qs = (
            Item.objects.filter(
                Q(name_ru__icontains=query)
                | Q(name_en__icontains=query)
                | Q(description_ru__icontains=query)
                | Q(description_en__icontains=query)
                | Q(slug__icontains=query)
                | Q(sku__icontains=query)
                | Q(material__icontains=query)
                | Q(technique__icontains=query)
                | Q(creation_year__icontains=query)
            )
            .filter(is_active=True)
            .distinct()
        )

        all_items = items_qs[:10]

        regular_items = [item for item in all_items if not item.is_art]
        artworks = [item for item in all_items if item.is_art]

        results["items"] = ItemListSerializer(
            regular_items, many=True, context={"request": request}
        ).data
        results["artworks"] = ItemListSerializer(
            artworks, many=True, context={"request": request}
        ).data

        # Поиск категорий
        categories = (
            Category.objects.filter(
                Q(name_ru__icontains=query)
                | Q(name_en__icontains=query)
                | Q(description_ru__icontains=query)
                | Q(description_en__icontains=query)
                | Q(slug__icontains=query)
            )
            .filter(is_active=True)
            .distinct()[:5]
        )
        results["categories"] = CategoryListSerializer(categories, many=True).data

        # Поиск авторов
        authors = Author.objects.filter(
            Q(name_ru__icontains=query)
            | Q(name_en__icontains=query)
            | Q(bio_ru__icontains=query)
            | Q(bio_en__icontains=query)
            | Q(slug__icontains=query)
        ).distinct()[:5]
        results["authors"] = AuthorListSerializer(authors, many=True).data

        # Поиск услуг
        services = (
            Service.objects.filter(
                Q(name_ru__icontains=query)
                | Q(name_en__icontains=query)
                | Q(description_ru__icontains=query)
                | Q(description_en__icontains=query)
                | Q(short_description_ru__icontains=query)
                | Q(short_description_en__icontains=query)
                | Q(slug__icontains=query)
            )
            .filter(is_active=True)
            .distinct()[:5]
        )
        results["services"] = ServiceListSerializer(services, many=True).data

        return Response(results)


class ItemPhotoViewSet(BaseCatalogViewSet):
    """ViewSet для управления фото товара"""

    queryset = ItemPhoto.objects.all()
    serializer_class = ItemPhotoSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item", "is_preview"]


class SpecPhotoViewSet(BaseCatalogViewSet):
    """ViewSet для управления фото характеристик"""

    queryset = SpecPhoto.objects.all()
    serializer_class = SpecPhotoSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["spec"]


class ServicePhotoViewSet(BaseCatalogViewSet):
    """ViewSet для управления фото услуг"""

    queryset = ServicePhoto.objects.all()
    serializer_class = ServicePhotoSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["service", "is_preview"]

    def get_permissions(self):
        """
        Только админы могут управлять фото услуг
        """
        return [permissions.IsAdminUser()]
