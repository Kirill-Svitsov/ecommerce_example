from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Favourite
from .serializers import (
    FavouriteSerializer,
    FavouriteCreateSerializer,
    FavouriteToggleMoodboardSerializer,
    FavouriteBulkReorderSerializer,
    FavouriteRemoveFromMoodboardSerializer,
)


class FavouriteViewSet(viewsets.ModelViewSet):
    """
    Избранное пользователя.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favourite.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return FavouriteCreateSerializer
        elif self.action == "toggle_moodboard":
            return FavouriteToggleMoodboardSerializer
        elif self.action == "remove_from_moodboard":
            return FavouriteRemoveFromMoodboardSerializer
        return FavouriteSerializer

    @action(detail=False, methods=["get"])
    def moodboard(self, request):
        """Список товаров в Moodboard"""
        queryset = self.get_queryset().filter(on_moodboard=True).order_by("moodboard_position")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def toggle_moodboard(self, request, pk=None):
        """Переключить видимость товара в Moodboard"""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data={"on_moodboard": not instance.on_moodboard}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(FavouriteSerializer(instance).data)

    @action(detail=True, methods=["delete"])
    def remove_from_moodboard(self, request, pk=None):
        """Удалить из Moodboard"""
        instance = self.get_object()
        instance.on_moodboard = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """Массовое обновление порядка"""
        serializer = FavouriteBulkReorderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        updated_favourites = Favourite.objects.filter(user=request.user).select_related("item")
        return Response(FavouriteSerializer(updated_favourites, many=True).data)

    @action(detail=False, methods=["get"])
    def ids(self, request):
        """Возвращает только ID товаров в избранном"""
        queryset = self.get_queryset().values_list("item_id", flat=True)
        return Response(list(queryset))

    @action(detail=False, methods=["get"])
    def moodboard_ids(self, request):
        """Возвращает только ID товаров в Moodboard"""
        queryset = self.get_queryset().filter(on_moodboard=True).values_list("item_id", flat=True)
        return Response(list(queryset))
