from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import generics, permissions, filters, serializers
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
import uuid
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from orders.models import DeliveryAddress
from orders.serializers import DeliveryAddressSerializer, DeliveryAddressAdminSerializer
from .constants import (
    VERIFICATION_CODE_EXPIRE_SECONDS,
    MAIL_SECONDS_LIMIT,
    MAX_VERIFICATION_EMAILS_PER_DAY,
    FRONTEND_URL,
)
from .serializers import (
    PasswordRecoverySerializer,
    ChangePasswordSerializer,
    UserListSerializer,
    AccountDeleteSerializer,
)
from .tasks import send_password_recovery_email

from tocco.logger import logger
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserDetailSerializer,
    EmailVerificationSerializer,
    ResendCodeSerializer,
    CustomTokenObtainPairSerializer,
)
from .utils import (
    generate_verification_code,
    store_verification_code,
    delete_verification_code,
    set_resend_timeout,
)
from .tasks import send_verification_code_email


class UserRegistrationView(generics.CreateAPIView):
    """Регистрация → отправка 6-значного кода."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(f"Регистрация: {user.email} - код отправлен")
        return Response(
            {"message": "Код подтверждения отправлен на email", "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class EmailVerificationView(generics.GenericAPIView):
    """Подтверждение email — активируем пользователя."""

    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.is_active = True
        user.save()
        delete_verification_code(user.email)
        logger.info(f"Email подтверждён: {user.email}")

        return Response({"message": "Email успешно подтверждён"}, status=status.HTTP_200_OK)


class ResendCodeView(generics.GenericAPIView):
    """Повторная отправка кода (таймаут 5 минут)."""

    serializer_class = ResendCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        code = generate_verification_code()
        store_verification_code(user.email, code)
        set_resend_timeout(user.email)
        send_verification_code_email.delay(user.email, code, user.first_name)
        logger.info(f"Код отправлен повторно: {user.email}")

        return Response({"message": "Новый код отправлен"}, status=status.HTTP_200_OK)


class UserDetailView(generics.RetrieveAPIView):
    """Профиль текущего пользователя"""

    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserUpdateView(generics.UpdateAPIView):
    """Обновление профиля"""

    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    """
    Логаут — добавление токенов в блэклист.
    Принимает оба токена (access и refresh) для полного выхода.
    """

    serializer_class = serializers.Serializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        access_token = request.data.get("access")
        errors = []
        # Добавляем refresh токен в блэклист
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError as e:
                errors.append(f"Refresh token: {str(e)}")
        # Access токен автоматически станет невалидным после истечения срока
        # (или при валидации, если refresh был в блэклисте)
        if access_token:
            try:
                AccessToken(access_token)
                # Access токен не имеет метода blacklist(), но он станет невалидным
                # когда сервер проверит его вместе с заблокированным refresh
            except TokenError as e:
                errors.append(f"Access token: {str(e)}")
        if errors:
            return Response(
                {"detail": "Частичный логаут", "errors": errors}, status=status.HTTP_200_OK
            )
        return Response({"detail": "Успешный выход"}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class PasswordRecoveryRequestView(APIView):
    """
    API View для запроса восстановления пароля.
    POST /api/users/password-recovery/
    """

    permission_classes = []
    authentication_classes = []

    @swagger_auto_schema(
        request_body=PasswordRecoverySerializer,
        responses={
            200: openapi.Response(
                description="Письмо отправлено",
                examples={
                    "application/json": {
                        "message": "Письмо для восстановления пароля отправлено",
                        "email": "user@example.com",
                        "recovery_id": "550e8400-e29b-41d4-a716-446655440000",
                        "attempts_left": 4,
                        "attempts_made": 1,
                    }
                },
            ),
            429: openapi.Response(description="Слишком много запросов"),
            400: openapi.Response(description="Ошибка валидации"),
        },
    )
    def post(self, request):
        serializer = PasswordRecoverySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"]
        # Ключи для кеша
        rate_limit_key = f"recovery_rate_limit:{email}"
        counter_key = f"recovery_counter:{email}"
        data_key = f"recovery_data:{email}"
        # 1. Проверяем rate limit (не чаще раза в минуту)
        last_sent = cache.get(rate_limit_key)
        if last_sent:
            time_passed = timezone.now() - last_sent
            if time_passed.total_seconds() < MAIL_SECONDS_LIMIT:
                wait_seconds = MAIL_SECONDS_LIMIT - int(time_passed.total_seconds())
                return Response(
                    {
                        "error": f"Письмо уже было отправлено. "
                        f"Попробуйте через {wait_seconds} секунд.",
                        "wait_seconds": wait_seconds,
                        "can_resend_after": (
                            timezone.now() + timedelta(seconds=wait_seconds)
                        ).isoformat(),
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
        # 2. Проверяем дневной лимит
        counter = cache.get(counter_key, 0)
        if counter >= MAX_VERIFICATION_EMAILS_PER_DAY:
            ttl = cache.ttl(counter_key)
            if ttl > 0:
                hours = ttl // 3600
                minutes = (ttl % 3600) // 60
                return Response(
                    {
                        "error": "Превышен лимит запросов на восстановление пароля",
                        "message": f"Лимит: {MAX_VERIFICATION_EMAILS_PER_DAY} запросов в день",
                        "reset_in_hours": hours,
                        "reset_in_minutes": minutes,
                        "reset_at": (timezone.now() + timedelta(seconds=ttl)).isoformat(),
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
        try:
            # 3. Генерируем recovery_id
            recovery_id = str(uuid.uuid4())
            recovery_key = f"password_recovery:{recovery_id}"
            # 4. Сохраняем данные в кеш
            recovery_data = {
                "email": email,
                "created_at": timezone.now().isoformat(),
                "used": False,
            }
            cache.set(recovery_key, recovery_data, timeout=VERIFICATION_CODE_EXPIRE_SECONDS)
            # 5. Обновляем счетчики
            counter = counter + 1
            cache.set(counter_key, counter, timeout=VERIFICATION_CODE_EXPIRE_SECONDS)
            cache.set(rate_limit_key, timezone.now(), timeout=MAIL_SECONDS_LIMIT)
            # 6. Сохраняем данные для повторной отправки
            recovery_meta = {
                "recovery_id": recovery_id,
                "email": email,
                "created_at": timezone.now().isoformat(),
            }
            cache.set(data_key, recovery_meta, timeout=VERIFICATION_CODE_EXPIRE_SECONDS)
            # 7. Формируем URL и отправляем письмо
            recovery_url = f"{FRONTEND_URL}/recovery/?verification_id={recovery_id}"
            send_password_recovery_email.delay(
                recipient_email=email,
                recovery_url=recovery_url,
                recovery_id=recovery_id,
            )
            logger.info(
                f"Password recovery email sent to {email}, "
                f"attempt {counter}/{MAX_VERIFICATION_EMAILS_PER_DAY}"
            )
            return Response(
                {
                    "message": "Письмо для восстановления пароля отправлено",
                    "email": email,
                    "recovery_id": recovery_id,
                    "attempts_left": MAX_VERIFICATION_EMAILS_PER_DAY - counter,
                    "attempts_made": counter,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error sending password recovery email: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "Ошибка при отправке письма",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChangePasswordView(APIView):
    """
    API View для установки нового пароля по verification_id.
    POST /api/users/change-password/
    """

    permission_classes = []
    authentication_classes = []

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Пароль изменен",
                examples={
                    "application/json": {
                        "message": "Пароль успешно изменен",
                        "email": "user@example.com",
                    }
                },
            ),
            400: openapi.Response(
                description="Ошибка валидации или недействительный токен",
                examples={
                    "application/json": {"errors": {"verification_id": ["Обязательное поле."]}}
                },
            ),
            404: openapi.Response(
                description="Пользователь не найден",
                examples={"application/json": {"error": "Пользователь не найден"}},
            ),
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        verification_id = serializer.validated_data["verification_id"]
        new_password = serializer.validated_data["user_password"]

        # Ключ для кеша
        recovery_key = f"password_recovery:{verification_id}"

        # Получаем данные из кеша
        recovery_data = cache.get(recovery_key)
        if not recovery_data:
            return Response(
                {
                    "error": "Ссылка для восстановления пароля недействительна или истекла",
                    "message": "Пожалуйста, запросите новое письмо",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Проверяем, не использована ли уже ссылка
        if recovery_data.get("used", False):
            return Response(
                {
                    "error": "Ссылка уже была использована",
                    "message": "Пожалуйста, запросите новое письмо",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Находим пользователя
            email = recovery_data["email"]
            user = User.objects.get(email=email)

            # Устанавливаем новый пароль
            user.set_password(new_password)
            user.save()

            # Отмечаем ссылку как использованную
            recovery_data["used"] = True
            recovery_data["used_at"] = timezone.now().isoformat()
            cache.set(recovery_key, recovery_data, timeout=VERIFICATION_CODE_EXPIRE_SECONDS)

            # Удаляем данные для повторной отправки
            data_key = f"recovery_data:{email}"
            cache.delete(data_key)

            # Очищаем счетчики
            cache.delete(f"recovery_counter:{email}")
            cache.delete(f"recovery_rate_limit:{email}")

            logger.info(f"Password changed successfully for user {email}")

            return Response(
                {
                    "message": "Пароль успешно изменен",
                    "email": email,
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            logger.error(f"User not found for email {email}")
            return Response(
                {"error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "Ошибка при смене пароля",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserListView(generics.ListAPIView):
    """Список всех пользователей (только для админа)"""

    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["created_at", "email", "is_active"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return User.objects.all().select_related().prefetch_related("groups")


class UserAdminDetailView(generics.RetrieveAPIView):
    """Детальная информация о любом пользователе (только для админа)"""

    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "id"
    lookup_url_kwarg = "user_id"
    queryset = User.objects.all()


class AccountDeleteView(APIView):
    """
    Удаление аккаунта текущим пользователем.
    Требует подтверждения паролем.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=AccountDeleteSerializer,
        responses={
            200: openapi.Response(
                description="Аккаунт удален",
                examples={"application/json": {"message": "Аккаунт успешно удален"}},
            ),
            400: openapi.Response(description="Ошибка валидации"),
            401: openapi.Response(description="Не авторизован"),
        },
    )
    def post(self, request):
        serializer = AccountDeleteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        email = user.email
        user.delete()

        logger.info(f"Account deleted: {email}")

        return Response({"message": "Аккаунт успешно удален"}, status=status.HTTP_200_OK)


class UserDeliveryAddressesView(generics.ListCreateAPIView):
    """
    Получение списка адресов доставки.
    - Обычный пользователь: видит только свои адреса
    - Администратор: может видеть все адреса с фильтрацией по user_id
    """

    serializer_class = DeliveryAddressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "is_default"]

    def get_queryset(self):
        user = self.request.user

        # Администратор может видеть все адреса
        if user.is_staff:
            queryset = DeliveryAddress.objects.all()
            # Фильтрация по user_id (если указан в query params)
            user_id = self.request.query_params.get("user_id")
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            return queryset

        # Обычный пользователь видит только свои адреса
        return DeliveryAddress.objects.filter(user=user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return DeliveryAddressAdminSerializer
        return DeliveryAddressSerializer

    def perform_create(self, serializer):
        user = self.request.user
        # Администратор может создавать адреса для других пользователей
        if user.is_staff and self.request.data.get("user_id"):
            target_user_id = self.request.data.get("user_id")
            target_user = User.objects.get(id=target_user_id)
            if serializer.validated_data.get("is_default"):
                DeliveryAddress.objects.filter(user=target_user, is_default=True).update(
                    is_default=False
                )
            serializer.save(user=target_user)
        else:
            if serializer.validated_data.get("is_default"):
                DeliveryAddress.objects.filter(user=user, is_default=True).update(is_default=False)
            serializer.save(user=user)


class UserDeliveryAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Получение, обновление, удаление конкретного адреса доставки.
    - Обычный пользователь: только свои адреса
    - Администратор: любые адреса
    """

    serializer_class = DeliveryAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DeliveryAddress.objects.all()
        return DeliveryAddress.objects.filter(user=user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return DeliveryAddressAdminSerializer
        return DeliveryAddressSerializer

    def perform_update(self, serializer):
        user = self.request.user
        address = self.get_object()

        # Если админ обновляет адрес другого пользователя
        if user.is_staff and address.user != user:
            if serializer.validated_data.get("is_default"):
                DeliveryAddress.objects.filter(user=address.user, is_default=True).exclude(
                    id=address.id
                ).update(is_default=False)
            serializer.save()
        else:
            if serializer.validated_data.get("is_default"):
                DeliveryAddress.objects.filter(user=user, is_default=True).exclude(
                    id=address.id
                ).update(is_default=False)
            serializer.save()
