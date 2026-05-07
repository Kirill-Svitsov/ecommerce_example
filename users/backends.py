from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    """
    Аутентификация по username (приоритет) или email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Поддерживаем оба поля
        if username is None:
            username = kwargs.get("email") or kwargs.get("username")
        # Сначала ищем по username (строгое совпадение)
        try:
            user = User.objects.get(username__exact=username)
        except User.DoesNotExist:
            # Если не нашли по username, пробуем по email
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                return None
        if user.check_password(password):
            return user
        return None
