import time

import requests

from tocco.logger import logger
from tocco.settings import (
    UNISENDER_API_KEY,
    UNISENDER_URL,
    DEFAULT_FROM_EMAIL,
    DEFAULT_REPLY_TO,
)


def send_verification_email(email, code, first_name=None):
    """
    Отправляет код подтверждения через Unisender Go.
    """
    name = first_name or "пользователь"
    payload = {
        "api_key": UNISENDER_API_KEY,
        "message": {
            "recipients": [{"email": email, "substitutions": {"CODE": code, "NAME": name}}],
            "body": {
                "html": f"""
                <h2>{name}, добро пожаловать в Tocco!</h2>
                <p>Ваш код подтверждения: <strong>{code}</strong></p>
                <p>Код действителен 1 час.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.
                </p>
                """,
                "plaintext": f"""
                {name}, добро пожаловать в Tocco!

                Ваш код подтверждения: {code}

                Код действителен 1 час.

                Это письмо отправлено автоматически.
                """,
            },
            "subject": "Код подтверждения Tocco",
            "from_email": DEFAULT_FROM_EMAIL,
            "from_name": "Tocco",
            "reply_to": DEFAULT_REPLY_TO,
            "track_links": 0,
            "track_read": 0,
            "global_language": "ru",
            "template_engine": "simple",
            "tags": ["verification"],
            "idempotence_key": f"verification_{email}_{code}_{int(time.time())}",
        },
    }
    try:
        logger.info(f"Unisender: отправка кода на {email}")
        clean_url = UNISENDER_URL.strip()
        response = requests.post(
            clean_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30
        )
        result = response.json()
        if response.status_code == 200:
            logger.info(f"Unisender: письмо отправлено {email} — {result.get('id', 'OK')}")
            return True
        else:
            logger.error(f"Unisender ошибка {response.status_code}: {result}")
            return False
    except Exception as e:
        logger.error(f"Unisender исключение: {str(e)}")
        return False


def send_password_recovery_email(email, recovery_url, recovery_id):
    """
    Отправляет письмо для восстановления пароля через Unisender Go.
    """
    import hashlib

    idempotence_key = hashlib.md5(f"{email}_{recovery_id}_{int(time.time())}".encode()).hexdigest()
    payload = {
        "api_key": UNISENDER_API_KEY,
        "message": {
            "recipients": [{"email": email}],
            "body": {
                "html": f"""
                <h2>Восстановление пароля в Tocco</h2>
                <p>Вы запросили восстановление пароля.
                Для создания нового пароля перейдите по ссылке:</p>
                <p><a href="{recovery_url}">{recovery_url}</a></p>
                <p>Ссылка действительна в течение 24 часов.</p>
                <p>Если вы не запрашивали восстановление пароля,
                просто проигнорируйте это письмо.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Это письмо отправлено автоматически.
                    Пожалуйста, не отвечайте на него.
                </p>
                """,
                "plaintext": f"""
                Восстановление пароля в Tocco

                Вы запросили восстановление пароля.
                Для создания нового пароля перейдите по ссылке:
                {recovery_url}

                Ссылка действительна в течение 24 часов.

                Если вы не запрашивали восстановление пароля,
                просто проигнорируйте это письмо.
                """,
            },
            "subject": "Восстановление пароля в Tocco",
            "from_email": DEFAULT_FROM_EMAIL,
            "from_name": "Tocco",
            "reply_to": DEFAULT_REPLY_TO,
            "track_links": 0,
            "track_read": 0,
            "global_language": "ru",
            "tags": ["password_recovery"],
            "idempotence_key": idempotence_key,
        },
    }

    try:
        logger.info(f"Unisender: отправка письма восстановления на {email}")
        clean_url = UNISENDER_URL.strip()
        response = requests.post(
            clean_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30
        )
        result = response.json()
        if response.status_code == 200:
            logger.info(
                f"Unisender: письмо восстановления отправлено {email} — {result.get('id', 'OK')}"
            )
            return True
        else:
            logger.error(f"Unisender ошибка {response.status_code}: {result}")
            return False
    except Exception as e:
        logger.error(f"Unisender исключение: {str(e)}")
        return False
