from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import CustomTokenObtainPairView

urlpatterns = [
    # Регистрация
    path("register/", views.UserRegistrationView.as_view(), name="user-register"),
    path("verify-email/", views.EmailVerificationView.as_view(), name="email-verify"),
    path("resend-code/", views.ResendCodeView.as_view(), name="resend-code"),
    path(
        "password-recovery/", views.PasswordRecoveryRequestView.as_view(), name="password-recovery"
    ),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("delete-account/", views.AccountDeleteView.as_view(), name="account-delete"),
    # JWT токены
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Профиль
    path("profile/", views.UserDetailView.as_view(), name="user-profile"),
    path("profile/update/", views.UserUpdateView.as_view(), name="user-profile-update"),
    # Адреса доставки
    path("addresses/", views.UserDeliveryAddressesView.as_view(), name="user-addresses"),
    path(
        "addresses/<int:pk>/",
        views.UserDeliveryAddressDetailView.as_view(),
        name="user-address-detail",
    ),
    # для админа
    path("list/", views.UserListView.as_view(), name="user-list"),
    path("admin/<int:user_id>/", views.UserAdminDetailView.as_view(), name="user-admin-detail"),
]
