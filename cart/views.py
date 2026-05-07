from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
)


class CartView(generics.RetrieveAPIView):
    """Получить корзину текущего пользователя (для админа - можно по ID)"""

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Админ может получить корзину по user_id из query params
        if self.request.user.is_staff:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                cart, _ = Cart.objects.get_or_create(user_id=user_id)
                cart.items.select_related("item", "size").prefetch_related(
                    "item__discounts",
                    "item__category__discounts",
                    "item__specs",
                    "item__specs__category",
                )
                return cart

        # По умолчанию - своя корзина
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        cart.items.select_related("item", "size").prefetch_related(
            "item__discounts", "item__category__discounts", "item__specs", "item__specs__category"
        )
        return cart


class CartListView(generics.ListAPIView):
    """Список всех корзин (только для админа)"""

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return (
            Cart.objects.all()
            .select_related("user")
            .prefetch_related(
                "items__item",
                "items__size",
                "items__item__discounts",
                "items__item__category__discounts",
                "items__item__specs",
                "items__item__specs__category",
            )
        )


class CartItemCreateView(generics.CreateAPIView):
    """Добавить товар в корзину"""

    serializer_class = CartItemCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


class CartItemUpdateView(generics.UpdateAPIView):
    """Обновить количество товара в корзине"""

    serializer_class = CartItemUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Админ может обновлять любые позиции (по запросу)
        if self.request.user.is_staff:
            cart_item_id = self.kwargs.get("pk")
            if cart_item_id:
                return CartItem.objects.filter(id=cart_item_id)

        # Обычный пользователь - только свои
        return CartItem.objects.filter(cart__user=self.request.user)


class CartItemDeleteView(generics.DestroyAPIView):
    """Удалить товар из корзины"""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Админ может удалять любые позиции
        if self.request.user.is_staff:
            cart_item_id = self.kwargs.get("pk")
            if cart_item_id:
                return CartItem.objects.filter(id=cart_item_id)

        # Обычный пользователь - только свои
        return CartItem.objects.filter(cart__user=self.request.user)


class CartClearView(APIView):
    """Очистить корзину"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        # Админ может очистить корзину любого пользователя
        if request.user.is_staff:
            user_id = request.query_params.get("user_id")
            if user_id:
                cart, _ = Cart.objects.get_or_create(user_id=user_id)
                cart.items.all().delete()
                return Response(
                    {"message": f"Корзина пользователя {user_id} очищена"},
                    status=status.HTTP_204_NO_CONTENT,
                )
        # По умолчанию - своя корзина
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({"message": "Корзина очищена"}, status=status.HTTP_204_NO_CONTENT)


class CartItemCountView(APIView):
    """Получить количество товаров в корзине (для бейджа)"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            user_id = request.query_params.get("user_id")
            if user_id:
                cart, _ = Cart.objects.get_or_create(user_id=user_id)
                total_items = cart.get_total_items()
                return Response({"count": total_items, "user_id": user_id})

        # По умолчанию - свой счетчик
        cart, _ = Cart.objects.get_or_create(user=request.user)
        total_items = cart.get_total_items()
        return Response({"count": total_items})
