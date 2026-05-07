from django.test import TestCase
from django.urls import reverse
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
        self.category = Category.objects.create(
            name_ru="Стулья", name_en="Chairs", slug="stulya", is_active=True
        )

        self.category2 = Category.objects.create(
            name_ru="Диваны", name_en="Sofas", slug="divany", is_active=True
        )

        self.author = Author.objects.create(
            name_ru="Мастерская Иванова", name_en="Ivanov Workshop", slug="ivanov-workshop"
        )

        self.spec_category = SpecCategory.objects.create(
            name_ru="Материал", name_en="Material", sort_order=1
        )

        self.item = Item.objects.create(
            name_ru="Стул Президент",
            slug="stul-prezident",
            category=self.category,
            author=self.author,
            base_price_rub=45000,
            base_price_usd=500,
            is_active=True,
        )

        self.item2 = Item.objects.create(
            name_ru="Стул Обычный",
            slug="stul-obichniy",
            category=self.category,
            author=self.author,
            base_price_rub=15000,
            base_price_usd=150,
            is_active=True,
        )

    def test_1_category_list_public(self):
        """Тест: список категорий доступен всем"""
        url = reverse("catalog:category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_2_create_category_as_admin(self):
        """Тест: админ может создать категорию"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("catalog:category-list")
        response = self.client.post(
            url,
            {
                "name_ru": "Кресла",
                "name_en": "Armchairs",
                "slug": "kresla",
                "sort_order": 2,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_3_create_category_as_user_forbidden(self):
        """Тест: обычный пользователь НЕ может создать категорию"""
        self.client.force_authenticate(user=self.user)
        url = reverse("catalog:category-list")
        response = self.client.post(url, {"name_ru": "Диваны", "slug": "divany"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_4_create_item_as_admin(self):
        """Тест: админ может создать товар"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("catalog:item-list")
        response = self.client.post(
            url,
            {
                "name_ru": "Стул Президент 2",
                "name_en": "President Chair 2",
                "slug": "stul-prezident-2",
                "category_id": self.category.id,
                "author_id": self.author.id,
                "base_price_rub": "45000.00",
                "base_price_usd": "500.00",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 3)

    def test_5_create_spec_as_admin(self):
        """Тест: админ может создать характеристику"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("catalog:spec-list")
        response = self.client.post(
            url,
            {
                "name_ru": "Натуральная кожа",
                "name_en": "Genuine leather",
                "category_id": self.spec_category.id,
                "item": self.item.id,
                "value_ru": "Кожа премиум",
                "value_en": "Premium leather",
                "price_modifier_rub": "25000.00",
                "price_modifier_usd": "280.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Spec.objects.count(), 1)

    # ✅ Дополнительные тесты
    def test_6_category_tree(self):
        """Тест: дерево категорий работает"""
        url = reverse("catalog:category-tree")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_7_item_list_filter_by_category(self):
        """Тест: фильтрация товаров по категории"""
        url = reverse("catalog:item-list")
        response = self.client.get(url, {"category": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_8_item_list_search(self):
        """Тест: поиск товаров"""
        url = reverse("catalog:item-list")
        response = self.client.get(url, {"search": "Президент"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name_ru"], "Стул Президент")

    def test_9_item_detail_not_found(self):
        """Тест: 404 для несуществующего товара"""
        url = reverse("catalog:item-detail", kwargs={"slug": "ne-sushestvuet"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_10_create_item_without_auth_forbidden(self):
        """Тест: без аутентификации нельзя создать товар"""
        url = reverse("catalog:item-list")
        response = self.client.post(
            url,
            {
                "name_ru": "Стул",
                "slug": "stul",
                "category_id": self.category.id,
                "base_price_rub": "10000.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
