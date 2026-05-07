from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .constants import HAS_MAIN_ARTICLE_LIMITS
from .models import Article, ArticleImage
from .serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateUpdateSerializer,
    ArticleImageSerializer,
)
from .pagination import BlogPagination


class ArticleImageViewSet(viewsets.ModelViewSet):
    """ViewSet для управления изображениями статей"""

    queryset = ArticleImage.objects.all()
    serializer_class = ArticleImageSerializer
    permission_classes = [permissions.IsAdminUser]


class ArticleViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для статей блога.
    - Публичные видят только опубликованные статьи
    - Админы могут создавать/редактировать/удалять
    """

    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title_ru", "title_en", "short_description_ru", "short_description_en"]
    ordering_fields = ["sort_order", "published_at", "created_at", "title_ru"]
    ordering = ["sort_order", "-published_at", "-created_at"]
    pagination_class = BlogPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = Article.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        exclude_main = self.request.query_params.get("exclude_main", "false").lower() == "true"
        if exclude_main:
            queryset = queryset.exclude(is_main=True)

        return queryset

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleListSerializer
        elif self.action == "retrieve":
            return ArticleDetailSerializer
        return ArticleCreateUpdateSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "exclude_main",
                openapi.IN_QUERY,
                description="Исключить главную статью из списка (true/false)",
                type=openapi.TYPE_BOOLEAN,
                default=False,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Номер страницы",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Количество элементов на странице",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Поиск по заголовкам и описанию",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Сортировка (sort_order, published_at, created_at, title_ru)",
                type=openapi.TYPE_STRING,
            ),
        ],
        operation_description="Получить список статей с возможностью исключить главную статью",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def get_main(self, request):
        """Получить главный пост"""
        article = Article.objects.filter(is_main=True, is_published=True).first()
        if article:
            serializer = ArticleDetailSerializer(article, context={"request": request})
            return Response(serializer.data)
        return Response({"detail": "Главный пост не найден"}, status=404)

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Последние статьи для главной (количество из константы)"""
        articles = self.get_queryset()[:HAS_MAIN_ARTICLE_LIMITS]
        serializer = ArticleListSerializer(articles, many=True, context={"request": request})
        return Response(serializer.data)
