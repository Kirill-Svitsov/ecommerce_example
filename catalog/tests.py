from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from catalog.models import Category, Author, Item, SpecCategory, Spec


class CatalogTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Создаём админа
        self.admin = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="admin123", is_active=True
        )

        # Создаём обычного пользователя
        self.user = User.objects.create_user(
            email="user@example.com", username="user", password="user123", is_active=True
        )

        # Создаём тестовые данные
        self.category = Category.objects.create(name_ru="Стулья", name_en="Chairs", slug="stulya")

        self.author = Author.objects.create(
            name_ru="Мастерская Иванова", name_en="Ivanov Workshop", slug="ivanov-workshop"
        )

        self.spec_category = SpecCategory.objects.create(
            name_ru="Материал", name_en="Material", sort_order=1
        )

    def test_1_category_list_public(self):
        """Тест: список категорий доступен всем"""
        response = self.client.get("/api/catalog/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_2_create_category_as_admin(self):
        """Тест: админ может создать категорию"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/catalog/categories/",
            {
                "name_ru": "Диваны",
                "name_en": "Sofas",
                "slug": "divany",
                "parent": None,
                "sort_order": 1,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_3_create_category_as_user_forbidden(self):
        """Тест: обычный пользователь НЕ может создать категорию"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/catalog/categories/", {"name_ru": "Диваны", "slug": "divany"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_4_create_item_as_admin(self):
        """Тест: админ может создать товар"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/catalog/items/",
            {
                "name_ru": "Стул Президент",
                "name_en": "President Chair",
                "slug": "stul-prezident",
                "category_id": self.category.id,
                "author_id": self.author.id,
                "base_price_rub": "45000.00",
                "base_price_usd": "500.00",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)

    def test_5_create_spec_as_admin(self):
        """Тест: админ может создать характеристику"""
        # Сначала создадим товар
        item = Item.objects.create(
            name_ru="Стул Президент",
            slug="stul-prezident",
            category=self.category,
            author=self.author,
            base_price_rub=45000,
            base_price_usd=500,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/catalog/specs/",
            {
                "name_ru": "Натуральная кожа",
                "name_en": "Genuine leather",
                "category_id": self.spec_category.id,
                "item": item.id,
                "value_ru": "Кожа премиум",
                "value_en": "Premium leather",
                "price_modifier_rub": "25000.00",
                "price_modifier_usd": "280.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Spec.objects.count(), 1)
