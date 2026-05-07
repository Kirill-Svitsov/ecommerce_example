# users/management/commands/seed_db.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from catalog.models import Category, Author, Item, Size, SpecCategory, Spec, Discount
from orders.models import DeliveryAddress, PromoCode, Order, OrderItem
from cart.models import Cart, CartItem
from favourites.models import Favourite
from blog.models import Article
import uuid
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Начинаю заполнение БД тестовыми данными..."))

        # =========================================================================
        # СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ
        # =========================================================================
        self.stdout.write("\nСоздаю пользователей...")

        users_data = [
            # Админы
            {
                "email": "admin@example.com",
                "username": "admin",
                "password": "admin123",
                "first_name": "Admin",
                "last_name": "Super",
                "phone": "+79990000001",
                "is_superuser": True,
                "is_staff": True,
                "is_subscribed": True,
            },
            # Обычные пользователи
            {
                "email": "ivan@example.com",
                "username": "ivan",
                "password": "user123",
                "first_name": "Иван",
                "last_name": "Петров",
                "phone": "+79991112233",
                "is_subscribed": True,
            },
            {
                "email": "maria@example.com",
                "username": "maria",
                "password": "user123",
                "first_name": "Мария",
                "last_name": "Иванова",
                "phone": "+79992223344",
                "is_subscribed": True,
            },
            {
                "email": "alex@example.com",
                "username": "alex",
                "password": "user123",
                "first_name": "Алексей",
                "last_name": "Смирнов",
                "phone": "+79993334455",
                "is_subscribed": False,
            },
            {
                "email": "elena@example.com",
                "username": "elena",
                "password": "user123",
                "first_name": "Елена",
                "last_name": "Козлова",
                "phone": "+79994445566",
                "is_subscribed": True,
            },
            {
                "email": "dmitry@example.com",
                "username": "dmitry",
                "password": "user123",
                "first_name": "Дмитрий",
                "last_name": "Волков",
                "phone": "+79995556677",
                "is_subscribed": False,
            },
        ]

        created_users = []
        for user_data in users_data:
            try:
                user = User.objects.get(email=user_data["email"])
                self.stdout.write(f"  - {user.email} уже существует")
            except User.DoesNotExist:
                # Генерируем уникальный username если нужно
                username = user_data["username"]
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{user_data['username']}_{counter}"
                    counter += 1

                if user_data.get("is_superuser"):
                    user = User.objects.create_superuser(
                        email=user_data["email"],
                        username=username,
                        password=user_data["password"],
                        first_name=user_data["first_name"],
                        last_name=user_data["last_name"],
                        phone=user_data["phone"],
                        is_active=True,
                        is_subscribed=user_data["is_subscribed"],
                    )
                else:
                    user = User.objects.create_user(
                        email=user_data["email"],
                        username=username,
                        password=user_data["password"],
                        first_name=user_data["first_name"],
                        last_name=user_data["last_name"],
                        phone=user_data["phone"],
                        is_active=True,
                        is_subscribed=user_data["is_subscribed"],
                    )
                self.stdout.write(f"  - Создан: {user.email}")
            created_users.append(user)
        users = created_users[1:]

        # =========================================================================
        # КАТЕГОРИИ
        # =========================================================================
        self.stdout.write("\nСоздаю категории...")

        # Сначала получаем или создаем корневые категории
        root_designer, _ = Category.objects.get_or_create(
            slug="designer-items",
            defaults={
                "name_ru": "Дизайнерские предметы",
                "name_en": "Designer items",
                "description_ru": "Коллекция дизайнерских предметов интерьера",
                "description_en": "Collection of designer interior items",
                "is_active": True,
                "sort_order": 1,
            },
        )

        root_art, _ = Category.objects.get_or_create(
            slug="art",
            defaults={
                "name_ru": "Арт",
                "name_en": "Art",
                "description_ru": "Коллекция произведений искусства",
                "description_en": "Collection of art pieces",
                "is_active": True,
                "sort_order": 2,
            },
        )

        self.stdout.write(f"  - Корневые категории: {root_designer.name_ru}, {root_art.name_ru}")

        # Теперь создаем подкатегории под этими корнями
        categories_data = [
            # Подкатегории для "Дизайнерские предметы"
            {
                "name_ru": "Диваны",
                "name_en": "Sofas",
                "slug": "divany",
                "parent": root_designer,
                "sort_order": 1,
                "children": [
                    {
                        "name_ru": "Угловые диваны",
                        "name_en": "Corner Sofas",
                        "slug": "uglovye-divany",
                    },
                    {
                        "name_ru": "Прямые диваны",
                        "name_en": "Straight Sofas",
                        "slug": "pryamye-divany",
                    },
                    {
                        "name_ru": "Модульные диваны",
                        "name_en": "Modular Sofas",
                        "slug": "modulnye-divany",
                    },
                    {"name_ru": "Диваны-кровати", "name_en": "Sofa Beds", "slug": "divany-krovati"},
                ],
            },
            {
                "name_ru": "Кресла",
                "name_en": "Armchairs",
                "slug": "kresla",
                "parent": root_designer,
                "sort_order": 2,
                "children": [
                    {
                        "name_ru": "Мягкие кресла",
                        "name_en": "Soft Armchairs",
                        "slug": "myagkie-kresla",
                    },
                    {
                        "name_ru": "Кресла-качалки",
                        "name_en": "Rocking Chairs",
                        "slug": "kresla-kachalki",
                    },
                    {
                        "name_ru": "Барные стулья",
                        "name_en": "Bar Stools",
                        "slug": "barnye-stulya",
                    },
                ],
            },
            {
                "name_ru": "Стулья",
                "name_en": "Chairs",
                "slug": "stulya",
                "parent": root_designer,
                "sort_order": 3,
                "children": [
                    {
                        "name_ru": "Обеденные стулья",
                        "name_en": "Dining Chairs",
                        "slug": "obedennye-stulya",
                    },
                    {
                        "name_ru": "Рабочие стулья",
                        "name_en": "Office Chairs",
                        "slug": "rabochie-stulya",
                    },
                ],
            },
            {
                "name_ru": "Столы",
                "name_en": "Tables",
                "slug": "stoly",
                "parent": root_designer,
                "sort_order": 4,
                "children": [
                    {
                        "name_ru": "Обеденные столы",
                        "name_en": "Dining Tables",
                        "slug": "obedennye-stoly",
                    },
                    {
                        "name_ru": "Журнальные столы",
                        "name_en": "Coffee Tables",
                        "slug": "zhurnalnye-stoly",
                    },
                    {
                        "name_ru": "Компьютерные столы",
                        "name_en": "Computer Desks",
                        "slug": "kompyuternye-stoly",
                    },
                ],
            },
            {
                "name_ru": "Кровати",
                "name_en": "Beds",
                "slug": "krovati",
                "parent": root_designer,
                "sort_order": 5,
                "children": [
                    {"name_ru": "Односпальные", "name_en": "Single Beds", "slug": "odnospalnye"},
                    {"name_ru": "Двуспальные", "name_en": "Double Beds", "slug": "dvuspalnye"},
                ],
            },
            # Подкатегории для "Арт"
            {
                "name_ru": "Картины",
                "name_en": "Paintings",
                "slug": "kartiny",
                "parent": root_art,
                "sort_order": 1,
                "children": [
                    {
                        "name_ru": "Масло",
                        "name_en": "Oil paintings",
                        "slug": "maslo",
                    },
                    {
                        "name_ru": "Акварель",
                        "name_en": "Watercolors",
                        "slug": "akvarel",
                    },
                ],
            },
            {
                "name_ru": "Скульптуры",
                "name_en": "Sculptures",
                "slug": "skulptury",
                "parent": root_art,
                "sort_order": 2,
                "children": [],
            },
            {
                "name_ru": "Графика",
                "name_en": "Graphics",
                "slug": "grafika",
                "parent": root_art,
                "sort_order": 3,
                "children": [],
            },
        ]

        categories = []
        for cat_data in categories_data:
            # Создаем родительскую подкатегорию (уровень 2)
            parent_cat, created = Category.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={
                    "name_ru": cat_data["name_ru"],
                    "name_en": cat_data["name_en"],
                    "parent": cat_data["parent"],  # Важно: привязываем к корню
                    "sort_order": cat_data["sort_order"],
                    "is_active": True,
                },
            )
            categories.append(parent_cat)
            self.stdout.write(
                f"  - {parent_cat.name_ru} (подкатегория {cat_data['parent'].name_ru})"
            )

            # Создаем подкатегории (уровень 3)
            for child_data in cat_data["children"]:
                child, created = Category.objects.get_or_create(
                    slug=child_data["slug"],
                    defaults={
                        "name_ru": child_data["name_ru"],
                        "name_en": child_data["name_en"],
                        "parent": parent_cat,
                        "is_active": True,
                    },
                )
                self.stdout.write(f"    - {child.name_ru}")
        # =========================================================================
        # АВТОРЫ
        # =========================================================================
        self.stdout.write("\nСоздаю авторов...")

        authors_data = [
            {
                "name_ru": "Иван Петров",
                "name_en": "Ivan Petrov",
                "slug": "ivan-petrov",
                "bio_ru": "Известный дизайнер мебели с 15-летним опытом. "
                "Работы находятся в частных коллекциях.",
                "bio_en": "Famous furniture designer with 15 years of experience.",
            },
            {
                "name_ru": "Мария Иванова",
                "name_en": "Maria Ivanova",
                "slug": "maria-ivanova",
                "bio_ru": "Архитектор и дизайнер интерьеров. "
                "Создает функциональную и красивую мебель.",
                "bio_en": "Architect and interior designer.",
            },
            {
                "name_ru": "Design Studio",
                "name_en": "Design Studio",
                "slug": "design-studio",
                "bio_ru": "Коллектив дизайнеров, " "специализирующихся на современной мебели.",
                "bio_en": "Team of designers specializing " "in contemporary furniture.",
            },
            {
                "name_ru": "Алексей Смирнов",
                "name_en": "Alexey Smirnov",
                "slug": "alexey-smirnov",
                "bio_ru": "Дизайнер-конструктор, создает " "эргономичную мебель для дома и офиса.",
                "bio_en": "Design engineer creating ergonomic furniture.",
            },
        ]

        authors = []
        for auth_data in authors_data:
            author, created = Author.objects.get_or_create(
                slug=auth_data["slug"],
                defaults={
                    "name_ru": auth_data["name_ru"],
                    "name_en": auth_data["name_en"],
                    "bio_ru": auth_data["bio_ru"],
                    "bio_en": auth_data["bio_en"],
                },
            )
            authors.append(author)
            self.stdout.write(f"  - {author.name_ru}")

        # =========================================================================
        # СКИДКИ
        # =========================================================================
        self.stdout.write("\nСоздаю скидки...")

        discounts_data = [
            {
                "name_ru": "Новогодняя распродажа",
                "name_en": "New Year Sale",
                "value": 15,
                "type": "percent",
                "is_active": True,
            },
            {
                "name_ru": "Черная пятница",
                "name_en": "Black Friday",
                "value": 20,
                "type": "percent",
                "is_active": True,
            },
            {
                "name_ru": "Скидка на диваны",
                "name_en": "Sofa Discount",
                "value": 10,
                "type": "percent",
                "is_active": True,
            },
            {
                "name_ru": "Фиксированная скидка",
                "name_en": "Fixed Discount",
                "value": 5000,
                "type": "fixed",
                "is_active": True,
            },
        ]

        discounts = []
        for disc_data in discounts_data:
            discount, created = Discount.objects.get_or_create(
                name_ru=disc_data["name_ru"],
                defaults={
                    "name_en": disc_data["name_en"],
                    "value": disc_data["value"],
                    "type": disc_data["type"],
                    "valid_from": timezone.now(),
                    "valid_to": timezone.now() + timezone.timedelta(days=30),
                    "is_active": disc_data["is_active"],
                },
            )
            discounts.append(discount)
            self.stdout.write(f"  - {discount.name_ru}")

        # =========================================================================
        # ТОВАРЫ
        # =========================================================================
        self.stdout.write("\nСоздаю товары...")

        items_data = [
            # Диваны
            {
                "name_ru": "Диван Честер",
                "name_en": "Chester Sofa",
                "slug": "divan-chester",
                "category": Category.objects.get(slug="divany"),
                "author": authors[0],
                "base_price_rub": 89900,
                "base_price_usd": 999,
                "description_ru": "Классический английский диван с "
                "глубокой посадкой. Обивка из премиального велюра.",
                "description_en": "Classic English sofa with deep seating.",
                "is_art": False,
                "discount": discounts[0],
            },
            {
                "name_ru": "Диван Комфорт",
                "name_en": "Comfort Sofa",
                "slug": "divan-komfort",
                "category": Category.objects.get(slug="divany"),
                "author": authors[2],
                "base_price_rub": 65000,
                "base_price_usd": 720,
                "description_ru": "Современный диван для ежедневного "
                "использования. Высокий уровень комфорта.",
                "description_en": "Modern sofa for daily use.",
                "is_art": False,
            },
            {
                "name_ru": "Диван Модульный",
                "name_en": "Modular Sofa",
                "slug": "divan-modulny",
                "category": Category.objects.get(slug="modulnye-divany"),
                "author": authors[1],
                "base_price_rub": 120000,
                "base_price_usd": 1330,
                "description_ru": "Модульная система, "
                "позволяющая создавать различные конфигурации.",
                "description_en": "Modular system for various configurations.",
                "is_art": False,
            },
            # Кресла
            {
                "name_ru": "Кресло Релакс",
                "name_en": "Relax Armchair",
                "slug": "kreslo-relaks",
                "category": Category.objects.get(slug="myagkie-kresla"),
                "author": authors[1],
                "base_price_rub": 35000,
                "base_price_usd": 390,
                "description_ru": "Удобное кресло для отдыха с регулируемой спинкой.",
                "description_en": "Comfortable armchair with adjustable back.",
                "is_art": False,
            },
            {
                "name_ru": "Кресло-качалка",
                "name_en": "Rocking Chair",
                "slug": "kreslo-kachalka",
                "category": Category.objects.get(slug="kresla-kachalki"),
                "author": authors[3],
                "base_price_rub": 45000,
                "base_price_usd": 500,
                "description_ru": "Классическое кресло-качалка из натурального дерева.",
                "description_en": "Classic wooden rocking chair.",
                "is_art": False,
            },
            # Стулья
            {
                "name_ru": "Стул Президент",
                "name_en": "President Chair",
                "slug": "stul-prezident",
                "category": Category.objects.get(slug="obedennye-stulya"),
                "author": authors[0],
                "base_price_rub": 45000,
                "base_price_usd": 500,
                "description_ru": "Элегантный стул с высокой спинкой. Ручная работа.",
                "description_en": "Elegant high-back chair. Handmade.",
                "is_art": True,
                "discount": discounts[2],
            },
            {
                "name_ru": "Стул офисный",
                "name_en": "Office Chair",
                "slug": "stul-ofisny",
                "category": Category.objects.get(slug="rabochie-stulya"),
                "author": authors[3],
                "base_price_rub": 25000,
                "base_price_usd": 280,
                "description_ru": "Эргономичное кресло для работы с регулировками.",
                "description_en": "Ergonomic office chair with adjustments.",
                "is_art": False,
            },
            # Столы
            {
                "name_ru": "Стол обеденный",
                "name_en": "Dining Table",
                "slug": "stol-obedenny",
                "category": Category.objects.get(slug="obedennye-stoly"),
                "author": authors[2],
                "base_price_rub": 55000,
                "base_price_usd": 610,
                "description_ru": "Стол из массива дуба на 6-8 персон.",
                "description_en": "Oak wood table for 6-8 persons.",
                "is_art": False,
            },
            {
                "name_ru": "Журнальный стол",
                "name_en": "Coffee Table",
                "slug": "zhurnalny-stol",
                "category": Category.objects.get(slug="zhurnalnye-stoly"),
                "author": authors[1],
                "base_price_rub": 18000,
                "base_price_usd": 200,
                "description_ru": "Стильный журнальный стол со стеклянной столешницей.",
                "description_en": "Stylish coffee table with glass top.",
                "is_art": False,
            },
            # Кровати
            {
                "name_ru": "Кровать двуспальная",
                "name_en": "Double Bed",
                "slug": "krovat-dvuspalnaya",
                "category": Category.objects.get(slug="dvuspalnye"),
                "author": authors[0],
                "base_price_rub": 95000,
                "base_price_usd": 1050,
                "description_ru": "Комфортная двуспальная кровать с подъемным механизмом.",
                "description_en": "Comfortable double bed with lifting mechanism.",
                "is_art": False,
            },
        ]

        items = []
        for item_data in items_data:
            discount = item_data.pop("discount", None) if "discount" in item_data else None
            item, created = Item.objects.get_or_create(
                slug=item_data["slug"],
                defaults={
                    **item_data,
                    "is_active": True,
                    "preview_photos": ["/media/items/preview.jpg"],
                    "photos": ["/media/items/photo1.jpg", "/media/items/photo2.jpg"],
                },
            )
            if created and discount:
                item.discounts.add(discount)
            items.append(item)
            self.stdout.write(f"  - {item.name_ru} ({item.base_price_rub} ₽)")

        # =========================================================================
        # РАЗМЕРЫ
        # =========================================================================
        self.stdout.write("\nСоздаю размеры...")

        sizes_data = [
            # Для диванов
            {
                "item": items[0],
                "value_ru": "2 места (160см)",
                "value_en": "2 seats",
                "price_multiplier": 1.0,
            },
            {
                "item": items[0],
                "value_ru": "3 места (210см)",
                "value_en": "3 seats",
                "price_multiplier": 1.3,
            },
            {
                "item": items[0],
                "value_ru": "Угловой",
                "value_en": "Corner",
                "price_multiplier": 1.5,
            },
            {
                "item": items[1],
                "value_ru": "2 места",
                "value_en": "2 seats",
                "price_multiplier": 1.0,
            },
            {
                "item": items[1],
                "value_ru": "3 места",
                "value_en": "3 seats",
                "price_multiplier": 1.3,
            },
            # Для кресел
            {
                "item": items[3],
                "value_ru": "Стандарт",
                "value_en": "Standard",
                "price_multiplier": 1.0,
            },
            # Для стульев
            {
                "item": items[5],
                "value_ru": "Стандарт",
                "value_en": "Standard",
                "price_multiplier": 1.0,
            },
            {
                "item": items[6],
                "value_ru": "Стандарт",
                "value_en": "Standard",
                "price_multiplier": 1.0,
            },
            # Для столов
            {
                "item": items[7],
                "value_ru": "160x80см",
                "value_en": "160x80cm",
                "price_multiplier": 1.0,
            },
            {
                "item": items[7],
                "value_ru": "180x90см",
                "value_en": "180x90cm",
                "price_multiplier": 1.2,
            },
            {
                "item": items[7],
                "value_ru": "200x100см",
                "value_en": "200x100cm",
                "price_multiplier": 1.4,
            },
            {
                "item": items[8],
                "value_ru": "80x80см",
                "value_en": "80x80cm",
                "price_multiplier": 1.0,
            },
            # Для кроватей
            {
                "item": items[9],
                "value_ru": "140x200см",
                "value_en": "140x200cm",
                "price_multiplier": 1.0,
            },
            {
                "item": items[9],
                "value_ru": "160x200см",
                "value_en": "160x200cm",
                "price_multiplier": 1.2,
            },
            {
                "item": items[9],
                "value_ru": "180x200см",
                "value_en": "180x200cm",
                "price_multiplier": 1.3,
            },
        ]

        for size_data in sizes_data:
            Size.objects.get_or_create(
                item=size_data["item"],
                value_ru=size_data["value_ru"],
                defaults={
                    "value_en": size_data["value_en"],
                    "price_multiplier": size_data["price_multiplier"],
                    "is_available": True,
                },
            )
        self.stdout.write("  - Создано размеров")

        # =========================================================================
        # КАТЕГОРИИ ХАРАКТЕРИСТИК
        # =========================================================================
        self.stdout.write("\nСоздаю категории характеристик...")

        spec_cats_data = [
            {"name_ru": "Материал обивки", "name_en": "Upholstery Material", "sort_order": 1},
            {"name_ru": "Цвет", "name_en": "Color", "sort_order": 2},
            {"name_ru": "Каркас", "name_en": "Frame", "sort_order": 3},
            {"name_ru": "Наполнитель", "name_en": "Filling", "sort_order": 4},
            {"name_ru": "Ножки", "name_en": "Legs", "sort_order": 5},
        ]

        spec_cats = []
        for sc_data in spec_cats_data:
            sc, created = SpecCategory.objects.get_or_create(
                name_ru=sc_data["name_ru"],
                defaults={"name_en": sc_data["name_en"], "sort_order": sc_data["sort_order"]},
            )
            spec_cats.append(sc)
            self.stdout.write(f"  - {sc.name_ru}")

        # =========================================================================
        # ХАРАКТЕРИСТИКИ
        # =========================================================================
        self.stdout.write("\nСоздаю характеристики...")

        specs_data = [
            # Для дивана Честер
            {
                "item": items[0],
                "category": spec_cats[0],
                "name_ru": "Обивка",
                "value_ru": "Велюр",
                "price_modifier_rub": 0,
                "price_modifier_usd": 0,
            },
            {
                "item": items[0],
                "category": spec_cats[0],
                "name_ru": "Обивка",
                "value_ru": "Натуральная кожа",
                "price_modifier_rub": 25000,
                "price_modifier_usd": 280,
            },
            {
                "item": items[0],
                "category": spec_cats[0],
                "name_ru": "Обивка",
                "value_ru": "Эко-кожа",
                "price_modifier_rub": 10000,
                "price_modifier_usd": 110,
            },
            {
                "item": items[0],
                "category": spec_cats[1],
                "name_ru": "Цвет",
                "value_ru": "Бежевый",
                "price_modifier_rub": 0,
            },
            {
                "item": items[0],
                "category": spec_cats[1],
                "name_ru": "Цвет",
                "value_ru": "Коричневый",
                "price_modifier_rub": 0,
            },
            {
                "item": items[0],
                "category": spec_cats[1],
                "name_ru": "Цвет",
                "value_ru": "Серый",
                "price_modifier_rub": 0,
            },
            # Для дивана Комфорт
            {
                "item": items[1],
                "category": spec_cats[0],
                "name_ru": "Обивка",
                "value_ru": "Рогожка",
                "price_modifier_rub": 0,
            },
            {
                "item": items[1],
                "category": spec_cats[0],
                "name_ru": "Обивка",
                "value_ru": "Велюр",
                "price_modifier_rub": 5000,
            },
            {
                "item": items[1],
                "category": spec_cats[2],
                "name_ru": "Каркас",
                "value_ru": "Массив сосны",
                "price_modifier_rub": 0,
            },
            {
                "item": items[1],
                "category": spec_cats[2],
                "name_ru": "Каркас",
                "value_ru": "Массив дуба",
                "price_modifier_rub": 15000,
            },
            # Для кресел
            {
                "item": items[3],
                "category": spec_cats[0],
                "name_ru": "Обивка",
                "value_ru": "Микрофибра",
                "price_modifier_rub": 0,
            },
            {
                "item": items[3],
                "category": spec_cats[3],
                "name_ru": "Наполнитель",
                "value_ru": "ППУ",
                "price_modifier_rub": 0,
            },
            {
                "item": items[3],
                "category": spec_cats[3],
                "name_ru": "Наполнитель",
                "value_ru": "Латекс",
                "price_modifier_rub": 8000,
            },
            # Для стола
            {
                "item": items[7],
                "category": spec_cats[2],
                "name_ru": "Материал столешницы",
                "value_ru": "Дуб",
                "price_modifier_rub": 0,
            },
            {
                "item": items[7],
                "category": spec_cats[2],
                "name_ru": "Материал столешницы",
                "value_ru": "Стекло",
                "price_modifier_rub": 5000,
            },
            {
                "item": items[7],
                "category": spec_cats[4],
                "name_ru": "Материал ножек",
                "value_ru": "Сталь",
                "price_modifier_rub": 0,
            },
            {
                "item": items[7],
                "category": spec_cats[4],
                "name_ru": "Материал ножек",
                "value_ru": "Дуб",
                "price_modifier_rub": 10000,
            },
        ]

        for spec_data in specs_data:
            Spec.objects.get_or_create(
                item=spec_data["item"],
                name_ru=spec_data["name_ru"],
                value_ru=spec_data["value_ru"],
                defaults={
                    "category": spec_data["category"],
                    "price_modifier_rub": spec_data.get("price_modifier_rub", 0),
                    "price_modifier_usd": spec_data.get(
                        "price_modifier_usd", round(spec_data.get("price_modifier_rub", 0) / 90, 2)
                    ),
                },
            )
        self.stdout.write("  - Создано характеристик")

        # =========================================================================
        # АДРЕСА ДОСТАВКИ
        # =========================================================================
        self.stdout.write("\nСоздаю адреса доставки...")

        addresses_data = [
            {
                "user": users[0],
                "label": "Дом",
                "address": "ул. Пушкина, д. 10",
                "entrance": "1",
                "floor": "5",
                "apartment": "50",
                "comment": "Домофон не работает",
                "is_default": True,
            },
            {
                "user": users[0],
                "label": "Работа",
                "address": "ул. Ленина, д. 5",
                "entrance": "2",
                "floor": "3",
                "apartment": "301",
                "comment": "Звонить за 30 минут",
                "is_default": False,
            },
            {
                "user": users[1],
                "label": "Дом",
                "address": "пр. Мира, д. 15",
                "entrance": "1",
                "floor": "2",
                "apartment": "15",
                "comment": "",
                "is_default": True,
            },
            {
                "user": users[2],
                "label": "Квартира",
                "address": "ул. Тверская, д. 3",
                "entrance": "3",
                "floor": "7",
                "apartment": "123",
                "comment": "Есть домофон",
                "is_default": True,
            },
            {
                "user": users[3],
                "label": "Дом",
                "address": "ул. Советская, д. 8",
                "entrance": "1",
                "floor": "1",
                "apartment": "8",
                "comment": "Первая дверь",
                "is_default": True,
            },
        ]

        for addr_data in addresses_data:
            DeliveryAddress.objects.get_or_create(
                user=addr_data["user"],
                label=addr_data["label"],
                defaults={
                    "address": addr_data["address"],
                    "entrance": addr_data["entrance"],
                    "floor": addr_data["floor"],
                    "apartment": addr_data["apartment"],
                    "comment": addr_data["comment"],
                    "has_elevator": True,
                    "requires_assemblers": False,
                    "is_default": addr_data["is_default"],
                },
            )
            self.stdout.write(f'  - {addr_data["label"]} для {addr_data["user"].email}')

        # =========================================================================
        # ПРОМОКОДЫ
        # =========================================================================
        self.stdout.write("\nСоздаю промокоды...")

        promos_data = [
            {"code": "WELCOME10", "description": "Скидка 10% для новых", "discount_percent": 10},
            {"code": "SALE2025", "description": "Скидка 15%", "discount_percent": 15},
            {
                "code": "FREEDEL",
                "description": "Бесплатная доставка",
                "discount_percent": 0,
                "discount_amount_rub": 500,
            },
            {"code": "SOFA20", "description": "Скидка на диваны 20%", "discount_percent": 20},
            {"code": "WINTER", "description": "Зимняя распродажа", "discount_percent": 25},
        ]

        for promo_data in promos_data:
            PromoCode.objects.get_or_create(
                code=promo_data["code"],
                defaults={
                    "description": promo_data["description"],
                    "discount_percent": promo_data.get("discount_percent", 0),
                    "discount_amount_rub": promo_data.get("discount_amount_rub", 0),
                    "valid_until": timezone.now().date() + timezone.timedelta(days=30),
                    "max_uses": 100,
                    "used_count": 0,
                    "is_active": True,
                },
            )
            self.stdout.write(f'  - {promo_data["code"]}')

        # =========================================================================
        # КОРЗИНЫ
        # =========================================================================
        self.stdout.write("\nСоздаю корзины...")

        for user in users[:3]:
            cart, created = Cart.objects.get_or_create(user=user)
            if not cart.items.exists():
                # Добавляем случайные товары в корзину
                num_items = random.randint(1, 3)
                selected_items = random.sample(items, min(num_items, len(items)))
                for item in selected_items:
                    size = Size.objects.filter(item=item).first()
                    CartItem.objects.create(
                        cart=cart,
                        item=item,
                        size=size,
                        quantity=random.randint(1, 2),
                        selected_spec_ids=[],
                        cached_price_rub=item.base_price_rub
                        * (size.price_multiplier if size else 1),
                        cached_price_usd=item.base_price_usd
                        * (size.price_multiplier if size else 1),
                    )
                self.stdout.write(f"  - Корзина для {user.email} заполнена")
            else:
                self.stdout.write(f"  - Корзина для {user.email} уже существует")

        # =========================================================================
        # ИЗБРАННОЕ
        # =========================================================================
        self.stdout.write("\nСоздаю избранное...")

        for user in users:
            fav_items = random.sample(items, random.randint(2, 5))
            for i, item in enumerate(fav_items):
                fav, created = Favourite.objects.get_or_create(
                    user=user,
                    item=item,
                    defaults={
                        "position": i,
                        "on_moodboard": random.choice([True, False]),
                        "moodboard_position": i if random.choice([True, False]) else 0,
                    },
                )
                if created:
                    self.stdout.write(f"  - {item.name_ru} добавлен в избранное для {user.email}")

        # =========================================================================
        # ЗАКАЗЫ
        # =========================================================================
        self.stdout.write("\nСоздаю заказы...")

        statuses = ["new", "confirmed", "paid", "assembling", "shipped", "delivered", "cancelled"]
        payment_statuses = ["pending", "paid", "failed", "refunded"]

        for user in users:
            # Создаем 2-4 заказа для каждого пользователя
            for _ in range(random.randint(2, 4)):
                # Случайные даты за последние 3 месяца
                created_days_ago = random.randint(1, 90)
                created_at = timezone.now() - timezone.timedelta(days=created_days_ago)

                status = random.choice(statuses)
                payment_status = random.choice(payment_statuses)

                # Выбираем товары для заказа
                order_items = random.sample(items, random.randint(1, 4))
                subtotal_rub = 0
                subtotal_usd = 0

                # Создаем заказ
                order = Order.objects.create(
                    user=user,
                    delivery_address=DeliveryAddress.objects.filter(user=user).first(),
                    email=user.email,
                    phone=user.phone,
                    full_name=f"{user.first_name} {user.last_name}",
                    delivery_instructions=random.choice(
                        ["Позвонить за час", "Оставить у двери", ""]
                    ),
                    delivery_cost_rub=random.choice([0, 500, 1000]),
                    delivery_cost_usd=random.choice([0, 6, 11]),
                    status=status,
                    payment_status=payment_status,
                    payment_method=random.choice(["card", "cash", "online"]),
                    payment_id=str(uuid.uuid4()) if payment_status == "paid" else "",
                    paid_at=(
                        created_at + timezone.timedelta(minutes=30)
                        if payment_status == "paid"
                        else None
                    ),
                    customer_comment=random.choice(
                        ["", "Позвоните перед доставкой", "Хочу получить в субботу"]
                    ),
                    created_at=created_at,
                )

                # Создаем товары в заказе
                for item in order_items:
                    size = Size.objects.filter(item=item).first()
                    price_rub = item.base_price_rub * (size.price_multiplier if size else 1)
                    price_usd = item.base_price_usd * (size.price_multiplier if size else 1)
                    quantity = random.randint(1, 2)

                    OrderItem.objects.create(
                        order=order,
                        item=item,
                        name=item.name_ru,
                        sku=item.sku or f"SKU-{item.id}",
                        size_value_ru=size.value_ru if size else "",
                        quantity=quantity,
                        price_rub=price_rub,
                        price_usd=price_usd,
                        total_rub=price_rub * quantity,
                        total_usd=price_usd * quantity,
                    )

                    subtotal_rub += price_rub * quantity
                    subtotal_usd += price_usd * quantity

                # Обновляем суммы заказа
                order.subtotal_rub = subtotal_rub
                order.subtotal_usd = subtotal_usd
                order.total_rub = subtotal_rub + order.delivery_cost_rub
                order.total_usd = subtotal_usd + order.delivery_cost_usd
                order.save()

                self.stdout.write(
                    f"  - Заказ {order.order_number} для {user.email} - {order.status}"
                )

        # =========================================================================
        # БЛОГ
        # =========================================================================
        self.stdout.write("\nСоздаю статьи блога...")

        articles_data = [
            {
                "title_ru": "Как выбрать идеальный диван",
                "title_en": "How to choose the perfect sofa",
                "short_description_ru": "Советы по выбору дивана для вашего интерьера",
                "short_description_en": "Tips for choosing a sofa for your interior",
                "description_ru": "Подробное руководство по выбору дивана. "
                "Рассматриваем материалы, размеры, механизмы трансформации...",
                "description_en": "Detailed guide on choosing a sofa.",
                "is_published": True,
                "published_at": timezone.now() - timezone.timedelta(days=5),
                "is_main": True,
            },
            {
                "title_ru": "Тренды мебели 2026",
                "title_en": "Furniture trends 2026",
                "short_description_ru": "Что будет модно в этом году",
                "short_description_en": "What will be fashionable this year",
                "description_ru": "Обзор главных трендов в дизайне мебели на 2026 год. "
                "Натуральные материалы, экологичность...",
                "description_en": "Overview of main furniture design trends for 2026.",
                "is_published": True,
                "published_at": timezone.now() - timezone.timedelta(days=12),
            },
            {
                "title_ru": "Материалы для обивки: плюсы и минусы",
                "title_en": "Upholstery materials: pros and cons",
                "short_description_ru": "Велюр, рогожка, кожа - что выбрать?",
                "short_description_en": "Velor, tapestry, leather - what to choose?",
                "description_ru": "Сравнение популярных материалов для "
                "обивки мягкой мебели. Износостойкость, уход, цена...",
                "description_en": "Comparison of popular upholstery materials.",
                "is_published": True,
                "published_at": timezone.now() - timezone.timedelta(days=18),
            },
            {
                "title_ru": "Как ухаживать за мебелью",
                "title_en": "How to care for furniture",
                "short_description_ru": "Простые правила продлят жизнь вашей мебели",
                "short_description_en": "Simple rules will extend the life of your furniture",
                "description_ru": "Советы по уходу за разными типами "
                "мебели и материалами. Чистка, защита от солнца...",
                "description_en": "Care tips for different types of furniture.",
                "is_published": True,
                "published_at": timezone.now() - timezone.timedelta(days=25),
            },
            {
                "title_ru": "Мебель для маленьких квартир",
                "title_en": "Furniture for small apartments",
                "short_description_ru": "Как обустроить компактное пространство",
                "short_description_en": "How to arrange a compact space",
                "description_ru": "Идеи и решения для небольших помещений. "
                "Трансформируемая мебель, многофункциональные предметы...",
                "description_en": "Ideas and solutions for small spaces.",
                "is_published": True,
                "published_at": timezone.now() - timezone.timedelta(days=32),
            },
            {
                "title_ru": "Дизайн интерьера: основные стили",
                "title_en": "Interior design: main styles",
                "short_description_ru": "Лофт, скандинавский, классика - в чем разница?",
                "short_description_en": "Loft, Scandinavian, classic - what's the difference?",
                "description_ru": "Обзор основных стилей интерьера "
                "и как подобрать мебель под каждый из них.",
                "description_en": "Overview of main interior styles and how to choose furniture.",
                "is_published": True,
                "published_at": timezone.now() - timezone.timedelta(days=40),
            },
        ]

        for article_data in articles_data:
            article, created = Article.objects.get_or_create(
                slug=slugify(article_data["title_ru"]), defaults=article_data
            )
            if created:
                self.stdout.write(f"  - {article.title_ru}")

        self.stdout.write(
            self.style.SUCCESS("\n✅ База данных успешно заполнена тестовыми данными!")
        )
