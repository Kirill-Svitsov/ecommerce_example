from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPagination(PageNumberPagination):
    """
    Кастомная пагинация с расширенной информацией:
    - per_page: количество элементов на странице
    - total_pages: общее количество страниц
    - current_page: текущая страница
    """

    page_size = 20  # количество элементов на странице по умолчанию
    page_size_query_param = "per_page"  # параметр для изменения количества элементов
    max_page_size = 100  # максимальное количество элементов на странице

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", self.page.number),
                    ("per_page", self.page.paginator.per_page),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )
