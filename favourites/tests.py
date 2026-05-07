from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from catalog.models import Category, Author, Item
from favourites.models import Favourite


class FavouriteTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="user@example.com", username="user", password="user123", is_active=True
        )
        self.client.force_authenticate(user=self.user)

        self.user2 = User.objects.create_user(
            email="user2@example.com", username="user2", password="user123", is_active=True
        )

        category = Category.objects.create(name_ru="Стулья", slug="stulya")
        author = Author.objects.create(name_ru="Мастерская Иванова", slug="ivanov-workshop")

        self.item1 = Item.objects.create(
            name_ru="Стул Президент 1",
            slug="stul-prezident-1",
            category=category,
            author=author,
            base_price_rub=45000,
            base_price_usd=500,
            is_active=True,
        )

        self.item2 = Item.objects.create(
            name_ru="Стул Президент 2",
            slug="stul-prezident-2",
            category=category,
            author=author,
            base_price_rub=55000,
            base_price_usd=600,
            is_active=True,
        )

        self.item3 = Item.objects.create(
            name_ru="Стул Президент 3",
            slug="stul-prezident-3",
            category=category,
            author=author,
            base_price_rub=65000,
            base_price_usd=700,
            is_active=True,
        )

    def test_1_add_to_favourites(self):
        """Добавление в избранное"""
        response = self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favourite.objects.count(), 1)
        self.assertEqual(response.data["item"], self.item1.id)

    def test_2_add_duplicate_fails(self):
        """Нельзя добавить один товар дважды"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        response = self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Favourite.objects.count(), 1)

    def test_3_list_favourites(self):
        """Список избранного"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        self.client.post("/api/favourites/", {"item": self.item2.id}, format="json")

        response = self.client.get("/api/favourites/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # В списке id есть
        self.assertIn("id", response.data["results"][0])

    def test_4_toggle_moodboard(self):
        """Переключение видимости в мудборде"""
        # Создаём запись
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")

        # Берём ID из базы (потому что в ответе POST его нет)
        fav = Favourite.objects.get(user=self.user, item=self.item1)
        fav_id = fav.id

        # Переключаем
        response = self.client.patch(
            f"/api/favourites/{fav_id}/toggle_moodboard/", {"on_moodboard": False}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["on_moodboard"])

    def test_5_remove_from_moodboard(self):
        """Удаление из мудборда (не из избранного)"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        fav = Favourite.objects.get(user=self.user, item=self.item1)
        fav_id = fav.id

        response = self.client.delete(f"/api/favourites/{fav_id}/remove_from_moodboard/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        fav.refresh_from_db()
        self.assertFalse(fav.on_moodboard)

    def test_6_reorder_all(self):
        """Массовое обновление порядка в общем списке"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        self.client.post("/api/favourites/", {"item": self.item2.id}, format="json")
        self.client.post("/api/favourites/", {"item": self.item3.id}, format="json")

        response = self.client.post(
            "/api/favourites/reorder/",
            {"type": "all", "order": [self.item3.id, self.item1.id, self.item2.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        favourites = Favourite.objects.filter(user=self.user).order_by("position")
        self.assertEqual(favourites[0].item_id, self.item3.id)
        self.assertEqual(favourites[1].item_id, self.item1.id)
        self.assertEqual(favourites[2].item_id, self.item2.id)

    def test_7_reorder_wrong_count_fails(self):
        """Ошибка при неверном количестве ID"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        self.client.post("/api/favourites/", {"item": self.item2.id}, format="json")

        response = self.client.post(
            "/api/favourites/reorder/",
            {"type": "all", "order": [self.item1.id]},  # должно быть 2 ID
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_8_reorder_other_user_fails(self):
        """Нельзя переставить чужие товары"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")

        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            "/api/favourites/reorder/", {"type": "all", "order": [self.item1.id]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_9_ids_endpoint(self):
        """Эндпоинт с ID товаров в избранном"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        self.client.post("/api/favourites/", {"item": self.item2.id}, format="json")

        response = self.client.get("/api/favourites/ids/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {self.item1.id, self.item2.id})

    def test_10_moodboard_ids(self):
        """Эндпоинт с ID товаров в мудборде"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        self.client.post("/api/favourites/", {"item": self.item2.id}, format="json")

        # Берём ID из базы
        fav2 = Favourite.objects.get(user=self.user, item=self.item2)
        fav2_id = fav2.id

        # Убираем второй товар из мудборда
        self.client.patch(
            f"/api/favourites/{fav2_id}/toggle_moodboard/", {"on_moodboard": False}, format="json"
        )

        response = self.client.get("/api/favourites/moodboard_ids/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [self.item1.id])

    def test_11_delete_from_favourites(self):
        """Полное удаление из избранного"""
        self.client.post("/api/favourites/", {"item": self.item1.id}, format="json")
        fav = Favourite.objects.get(user=self.user, item=self.item1)
        fav_id = fav.id

        response = self.client.delete(f"/api/favourites/{fav_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favourite.objects.count(), 0)
