import random
import string
from django.core.cache import cache
from tocco.logger import logger


def generate_verification_code(length=6):
    """Генерирует код из 6 цифр."""
    code = "".join(random.choices(string.digits, k=length))
    logger.debug(f"Сгенерирован код: {code}")
    return code


def store_verification_code(email, code):
    cache.set(f"verification_code:{email}", code, timeout=3600)
    logger.info(f"Redis SET: {email} = {code}")
    saved = cache.get(f"verification_code:{email}")
    if saved == code:
        logger.info(f"Redis OK: {email} = {saved}")
    else:
        logger.error(f"Redis FAIL: {email} - сохранено {saved}, ожидалось {code}")


def get_verification_code(email):
    """Получает код из Redis."""
    code = cache.get(f"verification_code:{email}")
    if code:
        logger.debug(f"Код получен из Redis: {email} -> {code}")
    else:
        logger.warning(f"Код не найден в Redis: {email}")
    return code


def delete_verification_code(email):
    """Удаляет код из Redis."""
    cache.delete(f"verification_code:{email}")
    logger.info(f"Код удалён из Redis: {email}")


def can_resend_code(email):
    """Проверяет, можно ли отправить код повторно (5 минут)."""
    key = f"resend_timeout:{email}"
    timeout_exists = cache.get(key) is not None
    if timeout_exists:
        logger.debug(f"Таймаут повторной отправки активен: {email}")
    else:
        logger.debug(f"Можно отправлять код повторно: {email}")
    return not timeout_exists


def set_resend_timeout(email):
    """Устанавливает таймаут на повторную отправку (5 минут)."""
    key = f"resend_timeout:{email}"
    cache.set(key, True, timeout=300)
    logger.info(f"Таймаут 5 минут установлен: {email}")
