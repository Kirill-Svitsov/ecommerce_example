from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register("", views.FavouriteViewSet, basename="favourite")

app_name = "favourites"

urlpatterns = [
    path("", include(router.urls)),
]
