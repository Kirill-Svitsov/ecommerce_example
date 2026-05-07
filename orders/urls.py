from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, DeliveryAddressViewSet, PromoCodeViewSet

router = DefaultRouter()

router.register(r"addresses", DeliveryAddressViewSet, basename="address")
router.register(r"promocodes", PromoCodeViewSet, basename="promocode")
router.register(r"", OrderViewSet, basename="order")

app_name = "orders"

urlpatterns = [
    path("", include(router.urls)),
]
