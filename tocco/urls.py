from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Tocco API",
        default_version="v1",
        description="API for furniture store",
        contact=openapi.Contact(email="admin@tocco.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/catalog/", include("catalog.urls", namespace="catalog")),
    path("api/cart/", include("cart.urls", namespace="cart")),
    path("api/favourites/", include("favourites.urls", namespace="favourites")),
    path("api/orders/", include("orders.urls", namespace="orders")),
    path("api/blog/", include("blog.urls")),
    path("api/contacts/", include("contacts.urls", namespace="contacts")),
    # Swagger
    path("swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
