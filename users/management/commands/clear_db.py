# users/management/commands/clear_db.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import Category, Author, Item, Size, SpecCategory, Spec, Discount
from orders.models import DeliveryAddress, PromoCode, Order, OrderItem, OrderService
from cart.models import Cart, CartItem
from favourites.models import Favourite
from blog.models import Article, ArticleImage

User = get_user_model()


class Command(BaseCommand):
    help = "Очищает базу данных от всех тестовых данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-users",
            action="store_true",
            help="Не удалять пользователей",
        )
        parser.add_argument(
            "--keep-superuser",
            action="store_true",
            help="Не удалять суперпользователя (по умолчанию True)",
        )
        parser.add_argument(
            "--keep-email",
            type=str,
            help="Сохранить пользователя с указанным email",
        )

    def handle(self, *args, **options):
        self.stdout.write("Начинаю очистку базы данных...")

        keep_superuser = options.get("keep_superuser", True)
        keep_users = options.get("keep_users", False)
        keep_email = options.get("keep_email")

        # Порядок важен из-за внешних ключей!
        models_to_clear = [
            (CartItem, "товаров в корзине"),
            (Cart, "корзин"),
            (OrderItem, "товаров в заказах"),
            (OrderService, "услуг в заказах"),
            (Order, "заказов"),
            (Favourite, "записей избранного"),
            (DeliveryAddress, "адресов доставки"),
            (PromoCode, "промокодов"),
            (Article, "статей блога"),
            (ArticleImage, "изображений блога"),
            (Discount, "скидок"),
            (Size, "размеров"),
            (Spec, "характеристик"),
            (SpecCategory, "категорий характеристик"),
            (Item, "товаров"),
            (Author, "авторов"),
            (Category, "категорий"),
        ]

        for model, name in models_to_clear:
            count = model.objects.all().delete()[0]
            self.stdout.write(f"  - Удалено {count} {name}")

        # Пользователей удаляем отдельно (с условиями)
        if not keep_users:
            users_to_delete = User.objects.all()

            if keep_superuser:
                super_users = users_to_delete.filter(is_superuser=True)
                super_count = super_users.count()
                users_to_delete = users_to_delete.exclude(is_superuser=True)
                if super_count > 0:
                    self.stdout.write(f"  - Сохранено {super_count} суперпользователей")

            if keep_email:
                try:

                    User.objects.get(email=keep_email)
                    users_to_delete = users_to_delete.exclude(email=keep_email)
                    self.stdout.write(f"  - Сохранён пользователь: {keep_email}")
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"  - Пользователь {keep_email} не найден")
                    )

            count = users_to_delete.delete()[0]
            self.stdout.write(f"  - Удалено {count} пользователей")
        else:
            self.stdout.write("  - Все пользователи сохранены")

        self.stdout.write(self.style.SUCCESS("✅ База данных успешно очищена!"))
