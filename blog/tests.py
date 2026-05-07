from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from blog.models import Article, ArticleImage
from blog.constants import HAS_MAIN_ARTICLE_LIMITS, NOT_MAIN_ARTICLE_LIMITS
import tempfile
from PIL import Image


class BlogTests(TestCase):
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

        # Создаём тестовое изображение
        self.image = self._create_test_image()

        # Создаём тестовые статьи
        self.articles = []
        for i in range(30):
            article = Article.objects.create(
                title_ru=f"Тестовая статья {i + 1}",
                title_en=f"Test article {i + 1}",
                short_description_ru=f"Краткое описание {i + 1}",
                short_description_en=f"Short description {i + 1}",
                description_ru=f"Полное содержание статьи {i + 1}",
                description_en=f"Full content of article {i + 1}",
                slug=f"test-article-{i + 1}",
                is_published=True,
                published_at=timezone.now() - timezone.timedelta(days=i),
                updated_at=timezone.now() - timezone.timedelta(hours=i),
            )
            self.articles.append(article)

    def _create_test_image(self):
        """Создаёт временное изображение для тестов"""
        image = tempfile.NamedTemporaryFile(suffix=".jpg")
        img = Image.new("RGB", (100, 100), color="red")
        img.save(image, format="JPEG")
        image.seek(0)
        return image

    # =========================================================================
    # ТЕСТЫ ПУБЛИЧНОГО ДОСТУПА
    # =========================================================================

    def test_1_list_articles_public(self):
        """Список статей доступен всем"""
        url = reverse("blog:article-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("has_is_main", response.data)
        self.assertIn("per_page", response.data)

    def test_2_article_detail_public(self):
        """Детальная статья доступна всем"""
        url = reverse("blog:article-detail", kwargs={"slug": "test-article-1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title_ru"], "Тестовая статья 1")
        self.assertIn("description_ru", response.data)

    def test_3_get_main_endpoint(self):
        """Эндпоинт получения главного поста"""
        # Назначаем главный пост
        self.articles[0].is_main = True
        self.articles[0].save()

        url = reverse("blog:article-get-main")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title_ru"], "Тестовая статья 1")
        self.assertTrue(response.data["is_main"])

    def test_4_get_main_not_found(self):
        """Когда нет главного поста - 404"""
        url = reverse("blog:article-get-main")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_5_latest_endpoint(self):
        """Последние статьи для главной"""
        url = reverse("blog:article-latest")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), HAS_MAIN_ARTICLE_LIMITS)

    # =========================================================================
    # ТЕСТЫ ПАГИНАЦИИ
    # =========================================================================

    def test_6_pagination_with_main_article(self):
        """Пагинация когда есть главный пост"""
        Article.objects.all().delete()
        for i in range(30):
            Article.objects.create(
                title_ru=f"Статья {i + 1}",
                slug=f"statya-{i + 1}",
                is_published=True,
                published_at=timezone.now() - timezone.timedelta(days=i),
            )
        main_article = Article.objects.order_by("published_at").last()
        main_article.is_main = True
        main_article.save()
        url = reverse("blog:article-list")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_is_main"])
        self.assertEqual(response.data["per_page"], HAS_MAIN_ARTICLE_LIMITS)
        self.assertEqual(len(response.data["results"]), HAS_MAIN_ARTICLE_LIMITS)
        self.assertEqual(response.data["results"][0]["is_main"], True)

    def test_7_pagination_without_main_article(self):
        """Пагинация когда нет главного поста"""
        url = reverse("blog:article-list")
        for page in [1, 2, 3]:
            response = self.client.get(url, {"page": page})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data["has_is_main"])
            self.assertEqual(response.data["per_page"], NOT_MAIN_ARTICLE_LIMITS)

    def test_8_pagination_page_size_parameter(self):
        """Параметр per_page работает"""
        url = reverse("blog:article-list")
        response = self.client.get(url, {"per_page": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["per_page"], 10)
        self.assertEqual(len(response.data["results"]), 10)

    # =========================================================================
    # ТЕСТЫ ПРАВ ДОСТУПА
    # =========================================================================

    def test_9_create_article_as_admin(self):
        """Админ может создать статью"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("blog:article-list")
        response = self.client.post(
            url, {"title_ru": "Новая статья", "is_published": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 31)

    def test_10_create_article_as_user_forbidden(self):
        """Обычный пользователь НЕ может создать статью"""
        self.client.force_authenticate(user=self.user)
        url = reverse("blog:article-list")
        response = self.client.post(
            url,
            {
                "title_ru": "Новая статья",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_11_update_article_as_admin(self):
        """Админ может обновить статью"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("blog:article-detail", kwargs={"slug": "test-article-1"})
        response = self.client.patch(url, {"title_ru": "Обновленный заголовок"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.articles[0].refresh_from_db()
        self.assertEqual(self.articles[0].title_ru, "Обновленный заголовок")

    def test_12_delete_article_as_admin(self):
        """Админ может удалить статью"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("blog:article-detail", kwargs={"slug": "test-article-1"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Article.objects.count(), 29)

    # =========================================================================
    # ТЕСТЫ ЛОГИКИ is_main И sort_order
    # =========================================================================

    def test_13_only_one_main_article(self):
        """Только один пост может быть главным"""
        self.client.force_authenticate(user=self.admin)

        # Делаем первый пост главным
        self.articles[0].is_main = True
        self.articles[0].save()
        self.assertEqual(self.articles[0].sort_order, 0)

        # Пытаемся сделать второй пост главным
        url = reverse("blog:article-detail", kwargs={"slug": "test-article-2"})
        response = self.client.patch(url, {"is_main": True}, format="json")

        # Должна быть ошибка валидации
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_main", str(response.data))

        # Проверяем, что первый остался главным
        self.articles[0].refresh_from_db()
        self.articles[1].refresh_from_db()
        self.assertTrue(self.articles[0].is_main)
        self.assertFalse(self.articles[1].is_main)

    def test_14_set_main_through_api(self):
        """Установка главного поста через API работает корректно"""
        self.client.force_authenticate(user=self.admin)

        url = reverse("blog:article-detail", kwargs={"slug": "test-article-1"})
        response = self.client.patch(url, {"is_main": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.articles[0].refresh_from_db()
        self.assertTrue(self.articles[0].is_main)
        self.assertEqual(self.articles[0].sort_order, 0)

    def test_15_sort_order_auto_assignment(self):
        """Автоматическое присвоение sort_order при создании"""
        # Первая статья
        article1 = Article.objects.create(title_ru="Статья 1", slug="statya-1", is_published=True)
        self.assertEqual(article1.sort_order, 1)
        # Вторая статья
        article2 = Article.objects.create(title_ru="Статья 2", slug="statya-2", is_published=True)
        self.assertEqual(article2.sort_order, 1)
        # Третья статья
        article3 = Article.objects.create(title_ru="Статья 3", slug="statya-3", is_published=True)
        self.assertEqual(article3.sort_order, 1)

    def test_16_sort_order_when_main_removed(self):
        """При снятии is_main, sort_order становится 1"""
        # Делаем статью главной
        self.articles[0].is_main = True
        self.articles[0].save()
        self.assertEqual(self.articles[0].sort_order, 0)

        # Снимаем главную
        self.articles[0].is_main = False
        self.articles[0].save()
        self.assertEqual(self.articles[0].sort_order, 1)

    # =========================================================================
    # ТЕСТЫ ПОИСКА И ФИЛЬТРАЦИИ
    # =========================================================================

    def test_17_search_articles(self):
        """Поиск по статьям работает"""
        # Создаем статью с уникальным названием
        Article.objects.create(
            title_ru="Уникальная статья для поиска", slug="unikalnaya-statya", is_published=True
        )

        url = reverse("blog:article-list")
        response = self.client.get(url, {"search": "Уникальная"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title_ru"], "Уникальная статья для поиска")

    def test_18_filter_unpublished_admin(self):
        """Админ видит неопубликованные статьи"""
        # Создаем неопубликованную статью
        Article.objects.create(
            title_ru="Неопубликованная", slug="neopublikovannaya", is_published=False
        )

        # Админ видит
        self.client.force_authenticate(user=self.admin)
        url = reverse("blog:article-list")
        response = self.client.get(url)
        slugs = [item["slug"] for item in response.data["results"]]
        self.assertIn("neopublikovannaya", slugs)

        # Обычный пользователь не видит
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        slugs = [item["slug"] for item in response.data["results"]]
        self.assertNotIn("neopublikovannaya", slugs)

    # =========================================================================
    # ТЕСТЫ ИЗОБРАЖЕНИЙ
    # =========================================================================

    def test_19_article_image_upload(self):
        """Загрузка изображения для статьи"""
        self.client.force_authenticate(user=self.admin)
        # Создаем статью
        article = Article.objects.create(
            title_ru="Тестовая статья для изображений",
            slug="test-article-for-images",
            is_published=True,
        )
        url = reverse("blog:articleimage-list")
        with open(self.image.name, "rb") as img:
            response = self.client.post(
                url,
                {"image": img, "caption_ru": "Тестовое изображение", "article": article.id},
                format="multipart",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("image_url", response.data)
        self.assertEqual(ArticleImage.objects.count(), 1)
        image = ArticleImage.objects.first()
        self.assertEqual(image.article.id, article.id)
        self.assertEqual(image.caption_ru, "Тестовое изображение")

    # =========================================================================
    # ТЕСТЫ СЛАГОВ
    # =========================================================================

    def test_20_slug_generation(self):
        """Автоматическая генерация слага работает"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("blog:article-list")
        # Отправляем запрос
        response = self.client.post(
            url, {"title_ru": "Статья с автоматическим слагом"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["slug"], "statya-s-avtomaticheskim-slagom")

    def test_21_duplicate_slug_fails(self):
        """Дубликат слага вызывает ошибку"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("blog:article-list")
        response1 = self.client.post(
            url, {"title_ru": "Статья с одинаковым названием"}, format="json"
        )
        response2 = self.client.post(
            url, {"title_ru": "Статья с одинаковым названием"}, format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response1.data["slug"], response2.data["slug"])
