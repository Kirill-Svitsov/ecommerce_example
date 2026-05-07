from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from users.models import User
from catalog.models import Category, Author, Item, Size
from cart.models import Cart, CartItem
from orders.models import Order, DeliveryAddress, PromoCode


class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Создаём пользователя
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="user123",
            is_active=True,
            phone="+79991234567",
            first_name="Иван",
            last_name="Петров",
        )
        self.client.force_authenticate(user=self.user)

        # Создаём второго пользователя
        self.user2 = User.objects.create_user(
            email="user2@example.com", username="user2", password="user123", is_active=True
        )

        # Создаём категорию и автора
        self.category = Category.objects.create(name_ru="Стулья", slug="stulya", is_active=True)

        self.author = Author.objects.create(name_ru="Мастерская Иванова", slug="ivanov-workshop")

        # Создаём товары
        self.item1 = Item.objects.create(
            name_ru="Стул Президент",
            slug="stul-prezident",
            category=self.category,
            author=self.author,
            base_price_rub=45000,
            base_price_usd=500,
            is_active=True,
            preview_photos=["/media/items/stul.jpg"],
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

        # Создаём размеры
        self.size1 = Size.objects.create(
            item=self.item1, value_ru="2 места", price_multiplier=1.0, is_available=True
        )

        self.size2 = Size.objects.create(
            item=self.item1, value_ru="3 места", price_multiplier=1.3, is_available=True
        )

        # Создаём корзину с товарами
        self.cart = Cart.objects.create(user=self.user)

        self.cart_item1 = CartItem.objects.create(
            cart=self.cart,
            item=self.item1,
            size=self.size2,
            quantity=1,
            selected_spec_ids=[],
            cached_price_rub=58500,  # 45000 * 1.3
            cached_price_usd=650,  # 500 * 1.3
        )

        # Создаём адрес доставки
        self.address = DeliveryAddress.objects.create(
            user=self.user,
            label="Дом",
            address="ул. Пушкина, д. 10",
            entrance="1",
            floor="5",
            apartment="50",
            comment="Домофон не работает",
            has_elevator=True,
            requires_assemblers=False,
            is_default=True,
        )

        # Создаём промокод
        self.promo = PromoCode.objects.create(
            code="SALE10",
            description="Скидка 10%",
            discount_percent=10,
            valid_until=timezone.now().date() + timezone.timedelta(days=30),
            max_uses=100,
            used_count=0,
            is_active=True,
        )

        self.expired_promo = PromoCode.objects.create(
            code="EXPIRED",
            description="Просроченный",
            discount_percent=20,
            valid_until=timezone.now().date() - timezone.timedelta(days=1),
            max_uses=100,
            used_count=0,
            is_active=True,
        )

    def test_1_list_addresses(self):
        """Список адресов пользователя"""
        DeliveryAddress.objects.all().delete()
        self.address = DeliveryAddress.objects.create(
            user=self.user,
            label="Дом",
            address="ул. Пушкина, д. 10",
            entrance="1",
            floor="5",
            apartment="50",
            comment="Домофон не работает",
            has_elevator=True,
            requires_assemblers=False,
            is_default=True,
        )
        url = reverse("orders:address-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["label"], "Дом")

    def test_2_create_address(self):
        """Создание нового адреса"""
        url = reverse("orders:address-list")
        response = self.client.post(
            url,
            {
                "label": "Работа",
                "address": "ул. Ленина, д. 5",
                "entrance": "2",
                "floor": "3",
                "apartment": "301",
                "comment": "Звонить за 30 минут",
                "has_elevator": True,
                "requires_assemblers": False,
                "is_default": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DeliveryAddress.objects.filter(user=self.user).count(), 2)
        self.assertIn("full_address", response.data)

    def test_3_set_default_address(self):
        """Установка адреса по умолчанию"""
        # Создаём второй адрес
        address2 = DeliveryAddress.objects.create(
            user=self.user, label="Работа", address="ул. Ленина, д. 5", is_default=False
        )

        url = reverse("orders:address-detail", args=[address2.id])
        response = self.client.patch(url, {"is_default": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что старый адрес больше не по умолчанию
        self.address.refresh_from_db()
        address2.refresh_from_db()
        self.assertFalse(self.address.is_default)
        self.assertTrue(address2.is_default)

    def test_4_other_user_address_not_accessible(self):
        """Нельзя получить доступ к чужому адресу"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("orders:address-detail", args=[self.address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_5_validate_promo_valid(self):
        """Проверка валидного промокода"""
        url = reverse("orders:promocode-validate")
        response = self.client.post(url, {"code": "SALE10"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "SALE10")
        self.assertEqual(response.data["discount_percent"], 10)
        self.assertTrue(response.data["valid"])

    def test_6_validate_promo_not_found(self):
        """Проверка несуществующего промокода"""
        url = reverse("orders:promocode-validate")
        response = self.client.post(url, {"code": "NOTFOUND"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)

    def test_7_validate_expired_promo(self):
        """Проверка просроченного промокода"""
        url = reverse("orders:promocode-validate")
        response = self.client.post(url, {"code": "EXPIRED"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_8_create_order(self):
        """Создание заказа из корзины"""
        url = reverse("orders:order-list")
        response = self.client.post(
            url,
            {
                "delivery_address_id": self.address.id,
                "delivery_instructions": "Звонить за час",
                "delivery_cost_rub": "500.00",
                "delivery_cost_usd": "5.00",
                "email": self.user.email,
                "phone": self.user.phone,
                "full_name": self.user.full_name,
                "payment_method": "card",
                "promo_code": "SALE10",
                "customer_comment": "Позвоните перед доставкой",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем создание заказа
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.status, "new")
        self.assertEqual(order.payment_status, "pending")
        self.assertEqual(order.promo_code_text, "SALE10")

        # Проверяем товары в заказе
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.name, "Стул Президент")
        self.assertEqual(order_item.quantity, 1)
        self.assertEqual(float(order_item.price_rub), 58500)  # 45000 * 1.3

        # Проверяем итоговые суммы (субтотал 58500 - 10% = 52650 + доставка 500 = 53150)
        self.assertEqual(float(order.total_rub), 53150)  # 58500 - 5850 + 500

        # Проверяем, что корзина очистилась
        self.assertEqual(self.cart.items.count(), 0)

        # Проверяем, что промокод использован
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)

    def test_9_create_order_without_address_fails(self):
        """Нельзя создать заказ без адреса"""
        url = reverse("orders:order-list")
        response = self.client.post(
            url,
            {
                "email": self.user.email,
                "phone": self.user.phone,
                "full_name": self.user.full_name,
                "payment_method": "card",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("address", str(response.data))

    def test_10_create_order_with_empty_cart_fails(self):
        """Нельзя создать заказ с пустой корзиной"""
        # Очищаем корзину
        self.cart.items.all().delete()

        url = reverse("orders:order-list")
        response = self.client.post(
            url,
            {
                "delivery_address_id": self.address.id,
                "email": self.user.email,
                "phone": self.user.phone,
                "full_name": self.user.full_name,
                "payment_method": "card",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_11_list_orders(self):
        """Список заказов пользователя"""
        Order.objects.all().delete()
        self.test_8_create_order()
        url = reverse("orders:order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_12_order_detail(self):
        """Детали заказа"""
        # Создаём заказ
        self.test_8_create_order()
        order = Order.objects.first()

        url = reverse("orders:order-detail", args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)
        self.assertIn("can_cancel", response.data)
        self.assertTrue(response.data["can_cancel"])
        self.assertFalse(response.data["can_refund"])

    def test_13_cancel_order(self):
        """Отмена заказа"""
        # Создаём заказ
        self.test_8_create_order()
        order = Order.objects.first()

        url = reverse("orders:order-cancel", args=[order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")

    def test_14_cancel_non_cancellable_order_fails(self):
        """Нельзя отменить заказ, который уже нельзя отменить"""
        # Создаём заказ
        self.test_8_create_order()
        order = Order.objects.first()

        # Меняем статус на оплачен
        order.status = "paid"
        order.save()

        url = reverse("orders:order-cancel", args=[order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_15_order_items_list(self):
        """Список товаров в заказе"""
        # Создаём заказ
        self.test_8_create_order()
        order = Order.objects.first()

        url = reverse("orders:order-items", args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Стул Президент")
        self.assertIn("specs_snapshot", response.data[0])

    def test_16_other_user_order_not_accessible(self):
        """Нельзя получить доступ к чужому заказу"""
        # Создаём заказ
        self.test_8_create_order()
        order = Order.objects.first()

        self.client.force_authenticate(user=self.user2)
        url = reverse("orders:order-detail", args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_17_create_order_with_text_address(self):
        """Создание заказа с текстовым адресом (без сохранённого)"""
        url = reverse("orders:order-list")
        response = self.client.post(
            url,
            {
                "delivery_address_text": "ул. Тестовая, д. 1, кв. 1",
                "delivery_instructions": "Позвонить",
                "email": self.user.email,
                "phone": self.user.phone,
                "full_name": self.user.full_name,
                "payment_method": "card",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.first()
        self.assertEqual(order.delivery_address_text, "ул. Тестовая, д. 1, кв. 1")
        self.assertIsNone(order.delivery_address)

    def test_18_create_order_without_promo(self):
        """Создание заказа без промокода"""
        url = reverse("orders:order-list")
        response = self.client.post(
            url,
            {
                "delivery_address_id": self.address.id,
                "email": self.user.email,
                "phone": self.user.phone,
                "full_name": self.user.full_name,
                "payment_method": "card",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.first()
        self.assertEqual(order.promo_code_text, "")
        self.assertEqual(float(order.discount_rub), 0)
        self.assertEqual(float(order.total_rub), 58500)
