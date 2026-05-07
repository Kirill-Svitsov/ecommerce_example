from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User


class UserAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/users/register/"
        self.login_url = "/api/users/login/"
        self.profile_url = "/api/users/profile/"

        self.user_data = {
            "email": "test@example.com",
            "password": "Test123!",
            "password_confirm": "Test123!",
            "first_name": "Тест",
            "last_name": "Тестов",
        }

    def test_1_register_user(self):
        """Тест регистрации нового пользователя"""
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Код подтверждения отправлен на email")
        user = User.objects.get(email="test@example.com")
        self.assertFalse(user.is_active)

    def test_2_login_inactive_user(self):
        self.client.post(self.register_url, self.user_data, format="json")
        response = self.client.post(
            self.login_url, {"email": "test@example.com", "password": "Test123!"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Аккаунт не активирован", str(response.data))

    def test_3_login_active_user(self):
        self.client.post(self.register_url, self.user_data, format="json")
        user = User.objects.get(email="test@example.com")
        user.is_active = True
        user.save()
        response = self.client.post(
            self.login_url, {"email": "test@example.com", "password": "Test123!"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
