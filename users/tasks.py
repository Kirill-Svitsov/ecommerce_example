from celery import shared_task

from tocco.logger import logger
from .unisender import send_verification_email, send_password_recovery_email as send_recovery


@shared_task
def send_verification_code_email(email, code, first_name=None):
    """Отправка кода через Unisender Go"""
    success = send_verification_email(email, code, first_name)
    if not success:
        logger.error(f"Unisender: не удалось отправить код на {email}")
    return success


@shared_task
def send_password_recovery_email(recipient_email, recovery_url, recovery_id):
    """Отправка письма для восстановления пароля"""
    success = send_recovery(recipient_email, recovery_url, recovery_id)
    if not success:
        logger.error(f"Failed to send password recovery email to {recipient_email}")
    return success
