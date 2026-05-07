from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

from blog.constants import HAS_MAIN_ARTICLE_LIMITS, NOT_MAIN_ARTICLE_LIMITS
from blog.models import Article


class BlogPagination(PageNumberPagination):
    """
    Кастомная пагинация для блога:
    - Если есть главный пост, на первой странице HAS_MAIN_ARTICLE_LIMITS постов
    - На остальных страницах по NOT_MAIN_ARTICLE_LIMITS постов
    - Если главного нет - везде по NOT_MAIN_ARTICLE_LIMITS постов
    - Можно переопределить через параметр per_page
    """

    page_size = NOT_MAIN_ARTICLE_LIMITS
    page_size_query_param = "per_page"
    max_page_size = 100

    def get_paginated_response(self, data):
        has_is_main = Article.objects.filter(is_main=True, is_published=True).exists()
        current_page = self.page.number
        per_page_param = self.request.query_params.get("per_page")
        if per_page_param:
            try:
                page_size = int(per_page_param)
            except ValueError:
                page_size = self.page_size
        elif has_is_main and current_page == 1:
            page_size = HAS_MAIN_ARTICLE_LIMITS
            # Обрезаем результаты до нужного размера
            if len(data) > page_size:
                data = data[:page_size]
        else:
            page_size = NOT_MAIN_ARTICLE_LIMITS
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", current_page),
                    ("per_page", page_size),
                    ("has_is_main", has_is_main),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )
