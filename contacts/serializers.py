import re

from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import Contact, Feedback


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор для контактов"""

    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class ContactUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления контактов (только админ)"""

    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "id"]


class FeedbackSerializer(serializers.ModelSerializer):
    """Сериализатор для обратной связи"""

    class Meta:
        model = Feedback
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]

    @staticmethod
    def validate_email(value):
        if not value:
            raise serializers.ValidationError("Email обязателен.")
        validator = EmailValidator("Некорректный формат email.")
        try:
            validator(value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc.message))
        return value

    @staticmethod
    def validate_phone(value):
        if not value:
            raise serializers.ValidationError("Телефон обязателен.")
        if not re.match(r"^[0-9\s+\-()]{5,20}$", value):
            raise serializers.ValidationError(
                "Телефон должен содержать только цифры и символы +, -, (, )."
            )
        return value

    @staticmethod
    def validate_message(value):
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Сообщение должно быть минимум 5 символов.")
        return value

    @staticmethod
    def validate_name(value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Имя должно быть минимум 2 символов.")
        return value
