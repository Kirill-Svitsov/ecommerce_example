from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.CartView.as_view(), name="cart-detail"),
    path("list/", views.CartListView.as_view(), name="cart-list"),
    path("items/", views.CartItemCreateView.as_view(), name="cart-item-create"),
    path("items/<int:pk>/", views.CartItemUpdateView.as_view(), name="cart-item-update"),
    path("items/<int:pk>/delete/", views.CartItemDeleteView.as_view(), name="cart-item-delete"),
    path("clear/", views.CartClearView.as_view(), name="cart-clear"),
    path("count/", views.CartItemCountView.as_view(), name="cart-count"),
]
