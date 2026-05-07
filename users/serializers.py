from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from .utils import (
    generate_verification_code,
    store_verification_code,
    get_verification_code,
    delete_verification_code,
    can_resend_code,
)
from .tasks import send_verification_code_email


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT токен с логином по email"""

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs.get("email"),
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError("Неверный email или пароль")
        if not user.is_active:
            raise ValidationError("Аккаунт не активирован. Подтвердите email.")

        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "is_active": user.is_active,
            },
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрация — отправляем код в Redis"""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
            "is_subscribed",
        )
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "phone": {"required": False},
            "is_subscribed": {"default": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data["is_active"] = False
        validated_data["username"] = validated_data["email"]
        user = User.objects.create_user(**validated_data)

        code = generate_verification_code()
        store_verification_code(user.email, code)
        send_verification_code_email.delay(user.email, code, user.first_name)
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Подтверждение email"""

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"], is_active=False)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден или уже активирован")

        stored_code = get_verification_code(user.email)
        if not stored_code:
            raise serializers.ValidationError({"code": "Код истёк или не существует"})
        if stored_code != attrs["code"]:
            raise serializers.ValidationError({"code": "Неверный код"})

        attrs["user"] = user
        return attrs


class ResendCodeSerializer(serializers.Serializer):
    """Повторная отправка кода"""

    email = serializers.EmailField()

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"], is_active=False)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден или уже активирован")

        if not can_resend_code(user.email):
            raise serializers.ValidationError("Повторная отправка доступна через 5 минут")

        attrs["user"] = user
        delete_verification_code(user.email)
        return attrs


class UserDetailSerializer(serializers.ModelSerializer):
    """Профиль пользователя"""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "is_subscribed",
            "is_staff",
            "is_superuser",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "email",
            "created_at",
            "updated_at",
            "is_staff",
            "is_superuser",
            "is_active",
        )


class PasswordRecoverySerializer(serializers.Serializer):
    """Сериализатор для запроса восстановления пароля"""

    email = serializers.EmailField(
        required=True,
        help_text=_("Email пользователя"),
    )

    def validate_email(self, value):
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError(_("Пользователь с таким email не найден"))
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""

    verification_id = serializers.UUIDField(
        required=True,
        help_text=_("ID верификации из письма"),
    )
    user_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text=_("Новый пароль (минимум 8 символов)"),
    )
    user_password_confirm = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text=_("Подтверждение пароля"),
    )

    def validate_user_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(_("Пароль должен содержать минимум 8 символов"))
        return value

    def validate(self, attrs):
        if attrs["user_password"] != attrs["user_password_confirm"]:
            raise serializers.ValidationError({"user_password_confirm": _("Пароли не совпадают")})
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка пользователей (для админа)"""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_subscribed",
            "created_at",
            "updated_at",
            "last_login",
        )
        read_only_fields = ("id", "created_at", "updated_at", "last_login")


class AccountDeleteSerializer(serializers.Serializer):
    """Сериализатор для подтверждения удаления аккаунта"""

    confirmation = serializers.BooleanField(
        required=True, help_text=_("Подтверждение удаления аккаунта (должно быть true)")
    )
    password = serializers.CharField(
        write_only=True, required=True, help_text=_("Пароль для подтверждения")
    )

    def validate_confirmation(self, value):
        if not value:
            raise serializers.ValidationError(_("Необходимо подтвердить удаление аккаунта"))
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError({"password": _("Неверный пароль")})
        return attrs
