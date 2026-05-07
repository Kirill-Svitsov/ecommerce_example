from django.urls import path
from . import views

app_name = "contacts"

urlpatterns = [
    path("", views.ContactDetailView.as_view(), name="contact-detail"),
    path("update/", views.ContactUpdateView.as_view(), name="contact-update"),
    path(
        "feedback/",
        views.FeedbackCreateView.as_view({"get": "list", "post": "create"}),
        name="feedback-list-create",
    ),
    path(
        "feedback/<int:pk>/",
        views.FeedbackCreateView.as_view({"get": "retrieve"}),
        name="feedback-detail",
    ),
]
