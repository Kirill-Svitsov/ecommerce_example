from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order, OrderItem, DeliveryAddress, PromoCode
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
    DeliveryAddressSerializer,
    PromoCodeSerializer,
    PromoCodeValidateSerializer,
    OrderItemSerializer,
)
from cart.models import Cart


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["status", "payment_status", "user"]
    ordering_fields = ["created_at", "total_rub"]
    ordering = ["-created_at"]
    search_fields = ["order_number", "email", "phone"]

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get("user", None)
        if user.is_staff:
            if user_id:
                return Order.objects.filter(user_id=user_id)
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        elif self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "user",
                openapi.IN_QUERY,
                description="ID пользователя (только для администраторов). "
                "Фильтр заказов по пользователю.",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Статус заказа",
                type=openapi.TYPE_STRING,
                enum=["new", "confirmed", "processing", "shipped", "delivered", "cancelled"],
            ),
            openapi.Parameter(
                "payment_status",
                openapi.IN_QUERY,
                description="Статус оплаты",
                type=openapi.TYPE_STRING,
                enum=["pending", "paid", "failed", "refunded"],
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Поле для сортировки (created_at, total_rub, -created_at, -total_rub)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Поиск по номеру заказа, email или телефону",
                type=openapi.TYPE_STRING,
            ),
        ],
        operation_description="Получить список заказов. "
        "Администраторы могут фильтровать по user_id.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Создание заказа из корзины"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart = Cart.objects.get(user=request.user)
            if not cart.items.exists():
                return Response({"error": "Корзина пуста"}, status=status.HTTP_400_BAD_REQUEST)

            order = self._create_order_from_cart(cart, serializer.validated_data, request)
            cart.items.all().delete()

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        except Cart.DoesNotExist:
            return Response({"error": "Корзина не найдена"}, status=status.HTTP_404_NOT_FOUND)

    def _create_order_from_cart(self, cart, validated_data, request):
        """Создаёт заказ из корзины"""
        from django.db import transaction

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                email=validated_data.get("email", request.user.email),
                phone=validated_data.get("phone", request.user.phone),
                full_name=validated_data.get("full_name", request.user.full_name),
                delivery_address_id=validated_data.get("delivery_address_id"),
                delivery_address_text=validated_data.get("delivery_address_text", ""),
                delivery_instructions=validated_data.get("delivery_instructions", ""),
                delivery_cost_rub=validated_data.get("delivery_cost_rub", 0),
                delivery_cost_usd=validated_data.get("delivery_cost_usd", 0),
                payment_method=validated_data.get("payment_method", "card"),
                promo_code_text=validated_data.get("promo_code", ""),
                customer_comment=validated_data.get("customer_comment", ""),
            )

            subtotal_rub = 0
            subtotal_usd = 0

            for cart_item in cart.items.select_related("item", "size").all():
                specs = cart_item.item.specs.filter(id__in=cart_item.selected_spec_ids)
                price_rub = cart_item.item.calculate_price(
                    size=cart_item.size, selected_specs=specs, currency="rub"
                )
                price_usd = cart_item.item.calculate_price(
                    size=cart_item.size, selected_specs=specs, currency="usd"
                )
                image_url = ""
                if cart_item.item.preview_photos and len(cart_item.item.preview_photos) > 0:
                    image_url = cart_item.item.preview_photos[0]

                OrderItem.objects.create(
                    order=order,
                    item=cart_item.item,
                    name=cart_item.item.name_ru,
                    sku=cart_item.item.sku,
                    size_value_ru=cart_item.size.value_ru if cart_item.size else "",
                    selected_spec_ids=cart_item.selected_spec_ids,
                    selected_specs_snapshot={},
                    image=image_url,
                    quantity=cart_item.quantity,
                    price_rub=price_rub,
                    price_usd=price_usd,
                    total_rub=price_rub * cart_item.quantity,
                    total_usd=price_usd * cart_item.quantity,
                )

                subtotal_rub += price_rub * cart_item.quantity
                subtotal_usd += price_usd * cart_item.quantity

            promo_discount_rub = 0
            promo_discount_usd = 0
            if validated_data.get("promo_code"):
                try:
                    promo = PromoCode.objects.get(code=validated_data["promo_code"], is_active=True)
                    if promo.discount_percent:
                        promo_discount_rub = subtotal_rub * promo.discount_percent / 100
                        promo_discount_usd = subtotal_usd * promo.discount_percent / 100
                    else:
                        promo_discount_rub = promo.discount_amount_rub
                        promo_discount_usd = promo.discount_amount_usd
                    order.promo_code = promo
                    order.promo_discount_rub = promo_discount_rub
                    order.promo_discount_usd = promo_discount_usd
                    promo.used_count += 1
                    promo.save()
                except PromoCode.DoesNotExist:
                    pass

            order.subtotal_rub = subtotal_rub
            order.subtotal_usd = subtotal_usd
            order.discount_rub = promo_discount_rub
            order.discount_usd = promo_discount_usd
            order.total_rub = subtotal_rub - promo_discount_rub + order.delivery_cost_rub
            order.total_usd = subtotal_usd - promo_discount_usd + order.delivery_cost_usd
            order.save()

            return order

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Отмена заказа"""
        order = self.get_object()
        if order.status not in ["new", "confirmed"]:
            return Response({"error": "Заказ нельзя отменить"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = "cancelled"
        order.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["get"])
    def items(self, request, pk=None):
        """Товары в заказе"""
        order = self.get_object()
        items = order.items.all()
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)


class DeliveryAddressViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ["-is_default", "-created_at"]

    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if serializer.validated_data.get("is_default"):
            DeliveryAddress.objects.filter(user=self.request.user, is_default=True).update(
                is_default=False
            )
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.validated_data.get("is_default"):
            DeliveryAddress.objects.filter(user=self.request.user, is_default=True).exclude(
                id=serializer.instance.id
            ).update(is_default=False)
        serializer.save()


class PromoCodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления промокодами.
    - Администраторы: полный CRUD (create, update, delete, list, retrieve)
    - Обычные пользователи: только проверка промокода (validate)
    """

    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    lookup_field = "code"  # Используем code вместо id для удобства

    def get_permissions(self):
        """
        Права доступа:
        - Для create, update, partial_update, destroy, list, retrieve - только админ
        - Для validate - любой авторизованный пользователь
        """
        if self.action in ["create", "update", "partial_update", "destroy", "list", "retrieve"]:
            return [permissions.IsAdminUser()]
        elif self.action == "validate":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """
        Для админов - все промокоды
        Для обычных пользователей - только активные (через validate)
        """
        if self.action == "validate":
            return PromoCode.objects.filter(is_active=True)
        return super().get_queryset()

    @action(detail=False, methods=["post"], url_path="validate")
    def validate(self, request):
        """
        Публичный метод для проверки промокода.
        Используется при оформлении заказа.
        """
        serializer = PromoCodeValidateSerializer(data=request.data)

        if serializer.is_valid():
            code = serializer.validated_data["code"]
            try:
                promo = PromoCode.objects.get(code=code, is_active=True)

                # Проверяем срок действия
                if promo.valid_until and promo.valid_until < timezone.now().date():
                    return Response(
                        {"valid": False, "error": "Срок действия промокода истек"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Проверяем лимит использований
                if promo.max_uses and promo.used_count >= promo.max_uses:
                    return Response(
                        {"valid": False, "error": "Лимит использований промокода исчерпан"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Возвращаем информацию о промокоде
                return Response(
                    {
                        "valid": True,
                        "code": promo.code,
                        "discount_percent": promo.discount_percent,
                        "discount_amount_rub": promo.discount_amount_rub,
                        "discount_amount_usd": promo.discount_amount_usd,
                        "description": promo.description,
                    }
                )

            except PromoCode.DoesNotExist:
                return Response(
                    {"valid": False, "error": "Промокод не найден"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"valid": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, code=None):
        """
        Применить промокод к заказу/корзине.
        (Опционально: можно сохранять в сессию или проверять перед созданием заказа)
        """
        try:
            promo = self.get_object()

            # Проверяем валидность
            if not promo.is_active:
                return Response({"error": "Промокод неактивен"}, status=status.HTTP_400_BAD_REQUEST)

            if promo.valid_until and promo.valid_until < timezone.now().date():
                return Response(
                    {"error": "Срок действия промокода истек"}, status=status.HTTP_400_BAD_REQUEST
                )

            if promo.max_uses and promo.used_count >= promo.max_uses:
                return Response(
                    {"error": "Лимит использований промокода исчерпан"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Здесь можно добавить логику применения к корзине/заказу
            # Например, сохранить промокод в сессии пользователя
            request.session["applied_promo"] = promo.code

            return Response(
                {
                    "success": True,
                    "message": "Промокод применен",
                    "code": promo.code,
                    "discount_percent": promo.discount_percent,
                    "discount_amount_rub": promo.discount_amount_rub,
                    "discount_amount_usd": promo.discount_amount_usd,
                }
            )

        except PromoCode.DoesNotExist:
            return Response({"error": "Промокод не найден"}, status=status.HTTP_404_NOT_FOUND)
