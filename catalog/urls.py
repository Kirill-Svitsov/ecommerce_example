from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Публичный роутер (/api/catalog/)
public_router = DefaultRouter()
public_router.register(r"categories", views.CategoryViewSet)
public_router.register(r"authors", views.AuthorViewSet)
public_router.register(r"items", views.ItemViewSet)
public_router.register(r"services", views.ServiceViewSet, basename="service")
public_router.register(r"spec-categories", views.SpecCategoryViewSet)
public_router.register(r"specs", views.SpecViewSet)
public_router.register(r"discounts", views.DiscountViewSet)
public_router.register(r"sizes", views.SizeViewSet)
public_router.register(r"item-photos", views.ItemPhotoViewSet)
public_router.register(r"spec-photos", views.SpecPhotoViewSet)
public_router.register(r"service-photos", views.ServicePhotoViewSet, basename="service-photo")

# Админский роутер (/admin-api/catalog/)
admin_router = DefaultRouter()
admin_router.register(r"categories", views.CategoryViewSet)
admin_router.register(r"authors", views.AuthorViewSet)
admin_router.register(r"items", views.ItemViewSet)
admin_router.register(r"services", views.ServiceViewSet, basename="service")
admin_router.register(r"spec-categories", views.SpecCategoryViewSet)
admin_router.register(r"specs", views.SpecViewSet)
admin_router.register(r"discounts", views.DiscountViewSet)
admin_router.register(r"sizes", views.SizeViewSet)

app_name = "catalog"

urlpatterns = [
    # Публичные URL
    path("", include(public_router.urls)),
    path("search/", views.GlobalSearchView.as_view(), name="global-search"),
]
