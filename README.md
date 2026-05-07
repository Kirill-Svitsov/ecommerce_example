# TOCCO API Documentation

Backend для интернет-магазина мебели TOCCO.

Содержание

    Утилиты

    1. Аутентификация и регистрация

    2. Каталог товаров

    3. Избранное и Moodboard

    4. Корзина

    5. Адреса доставки

    6. Промокоды

    7. Заказы

    8. Услуги

    9. Глобальный поиск

    10. Коды ответов

    11. Пагинация

## Утилиты

- Заполнение БД тестовыми данными

```
docker exec -it tocco_backend python manage.py seed_db
```

- Очистка БД от тестовых данных

```
# Очистить всё, но сохранить пользователя с указанным email
docker exec -it tocco_backend python manage.py clear_db --keep-email example@gmail.com
```

```
# Сохранить всех суперпользователей
docker exec -it tocco_backend python manage.py clear_db --keep-superuser
```

```
# Сохранить всех пользователей
docker exec -it tocco_backend python manage.py clear_db --keep-users
```

# TOCCO Backend - Инструкция по развертыванию

## 1. Локальный запуск (разработка)

### 1.1 Настройка переменных окружения

Создайте файл .env в корне проекта:

```
# Django
SECRET_KEY=your_secret_key
DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
POSTGRES_DB=db_name
POSTGRES_USER=db_user
POSTGRES_PASSWORD=db_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/1

# Celery
CELERY_BROKER_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
CELERY_RESULT_BACKEND=redis://${REDIS_HOST}:${REDIS_PORT}/0

# Unisender (для отправки email)
DEFAULT_FROM_EMAIL=noreply@souldev.site
DEFAULT_TO_EMAIL=support@tsouldev.site
UNISENDER_API_KEY=your_api_key

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend URL (для ссылок в письмах)
FRONTEND_URL=http://localhost:3000
```

### 1.2 Запуск проекта

```
# Сборка и запуск контейнеров
docker compose up --build -d

# Применение миграций
docker exec -it tocco_backend python manage.py migrate

# Заполнение тестовыми данными (опционально)
docker exec -it tocco_backend python manage.py seed_db

# Сбор статики
docker exec -it tocco_backend python manage.py collectstatic --noinput
```

### Доступные сервисы

    Backend API: http://localhost:8000

    Админка Django: http://localhost:8000/admin

    Swagger документация: http://localhost:8000/swagger

    ReDoc: http://localhost:8000/redoc

    База данных: localhost:5432

    Redis: localhost:6379

### Тесты

```
docker exec -it tocco_backend python manage.py test
```

## 2. Продакшн-развертывание

### 2.1 Подготовка сервера

```
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

### 2.2 Клонирование и настройка

```
git clone <url-репозитория>
cd tocco_backend
```

### 2.3 Продакшн-конфигурация

Создайте файл .env.prod:

```
# Django
SECRET_KEY=your-very-strong-secret-key-here
DEBUG=0
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
POSTGRES_DB=tocco_db
POSTGRES_USER=tocco_user
POSTGRES_PASSWORD=very-strong-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/1

# Celery
CELERY_BROKER_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
CELERY_RESULT_BACKEND=redis://${REDIS_HOST}:${REDIS_PORT}/0

# Unisender (для отправки email)
DEFAULT_FROM_EMAIL=noreply@your-domain.com
DEFAULT_TO_EMAIL=support@your-domain.com
UNISENDER_API_KEY=your-unisender-api-key

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Frontend URL (для ссылок в письмах)
FRONTEND_URL=https://your-domain.com

# CSRF
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### 2.4 Запуск в продакшн-режиме

```
# Используем продакшн-конфигурацию
docker compose -f docker-compose.prod.yml up --build -d

# Применение миграций
docker exec -it tocco_backend python manage.py migrate

# Сбор статики
docker exec -it tocco_backend python manage.py collectstatic --noinput

# Создание суперпользователя
docker exec -it tocco_backend python manage.py createsuperuser
```

### 2.5 Настройка SSL (Let's Encrypt)

```
# Установка certbot
sudo apt-get install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

```
tocco_backend/
├── blog/                 # Блог
├── cart/                 # Корзина
├── catalog/              # Каталог товаров
├── contacts/             # Контакты
├── favourites/           # Избранное
├── orders/               # Заказы
├── users/                # Пользователи
├── tocco/                # Основные настройки
├── docker/               # Docker-файлы
│   ├── backend.Dockerfile
│   ├── entrypoint.sh
│   └── nginx.conf
├── docker-compose.yml    # Локальный запуск
├── docker-compose.prod.yml # Продакшн-запуск
├── requirements.txt      # Зависимости Python
├── .env                  # Локальные переменные
├── .env.prod             # Продакшн-переменные
└── manage.py             # Django-менеджер
```

## Эндпоинты

## 1. АУТЕНТИФИКАЦИЯ И РЕГИСТРАЦИЯ

### 1.1 Регистрация нового пользователя

POST /api/users/register/
Запрос:

```
{
  "email": "ivan@example.com",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!",
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+79991234567",
  "is_subscribed": true
}
```

Ответ (201 Created):

```
{
  "message": "Код подтверждения отправлен на email",
  "email": "ivan@example.com"
}
```

⚠️ Пользователь создаётся с is_active=False до подтверждения email.

### 1.2 Подтверждение email

POST /api/users/verify-email/
Запрос:

```
{
  "email": "ivan@example.com",
  "code": "123456"
}
```

Ответ (200 OK):

```
{
  "message": "Email успешно подтверждён"
}
```

### 1.3 Получение JWT токенов (Логин)

POST /api/users/login/
Запрос:

```
{
  "email": "ivan@example.com",
  "password": "StrongPass123!"
}
```

Ответ (200 OK):

```
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "ivan@example.com",
    "first_name": "Иван",
    "last_name": "Петров"
  }
}
```

### 1.4 Обновление токена (когда access истёк)

POST /api/users/token/refresh/
Запрос:

```
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Ответ (200 OK):

```{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 1.5 Получение профиля

GET /api/users/profile/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):

```
{
  "id": 1,
  "email": "ivan@example.com",
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+79991234567",
  "is_subscribed": true,
  "created_at": "2025-02-19T10:00:00Z",
  "updated_at": "2025-02-19T10:00:00Z"
}
```

### 1.6 Обновление профиля

PATCH /api/users/profile/

Headers: Authorization: Bearer <access_token>

Запрос:

```
{
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+79991234567"
}
```

Ответ (200 OK):

```
{
  "id": 1,
  "email": "ivan@example.com",
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+79991234567",
  "is_subscribed": true,
  "created_at": "2025-02-19T10:00:00Z",
  "updated_at": "2025-02-19T10:05:00Z"
}
```

### 1.7 Логаут

POST /api/users/logout/

Headers: Authorization: Bearer <access_token>

Запрос:

```
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Ответ (200 OK):

```
{
  "detail": "Успешный выход"
}
```

### 1.8 Запрос на восстановление пароля

POST /api/users/password-recovery/

Запрос:
json
```
{
  "email": "ivan@example.com"
}
```
Ответ (200 OK):
json
```
{
  "message": "Письмо для восстановления пароля отправлено",
  "email": "ivan@example.com",
  "recovery_id": "550e8400-e29b-41d4-a716-446655440000",
  "attempts_left": 4,
  "attempts_made": 1
}
```
Ответ (429 Too Many Requests):
json
```
{
  "error": "Письмо уже было отправлено. Попробуйте через 60 секунд.",
  "wait_seconds": 60
}
```
### 1.9 Смена пароля по verification_id

POST /api/users/change-password/

Запрос:
json
```
{
  "verification_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_password": "NewPass123!",
  "user_password_confirm": "NewPass123!"
}
```
Ответ (200 OK):
json
```
{
  "message": "Пароль успешно изменен",
  "email": "ivan@example.com"
}
```
Ответ (400 Bad Request) - недействительный токен:
json
```
{
  "error": "Ссылка для восстановления пароля недействительна или истекла"
}
```

## 2. КАТАЛОГ ТОВАРОВ

### 2.1 Дерево категорий

GET /api/catalog/categories/tree/
Ответ (200 OK):

```
[
  {
    "id": 1,
    "name_ru": "Диваны",
    "name_en": "Sofas",
    "slug": "divany",
    "is_active": true,
    "items_count": 15,
    "children": [
      {
        "id": 3,
        "name_ru": "Угловые диваны",
        "name_en": "Corner Sofas",
        "slug": "uglovye-divany",
        "is_active": true,
        "items_count": 5,
        "children": []
      },
      {
        "id": 4,
        "name_ru": "Прямые диваны",
        "name_en": "Straight Sofas",
        "slug": "pryamye-divany",
        "is_active": true,
        "items_count": 10,
        "children": []
      }
    ]
  },
  {
    "id": 2,
    "name_ru": "Кресла",
    "name_en": "Chairs",
    "slug": "kresla",
    "is_active": true,
    "items_count": 8,
    "children": []
  }
]
```

### 2.2 Список категорий (только корневые)

GET /api/catalog/categories/
Ответ (200 OK):

```
[
  {
    "id": 1,
    "name_ru": "Диваны",
    "name_en": "Sofas",
    "slug": "divany",
    "parent": null,
    "sort_order": 1,
    "is_active": true,
    "children_count": 3,
    "items_count": 15
  },
  {
    "id": 2,
    "name_ru": "Кресла",
    "name_en": "Chairs",
    "slug": "kresla",
    "parent": null,
    "sort_order": 2,
    "is_active": true,
    "children_count": 0,
    "items_count": 8
  }
]
```

### 2.3 Детальная категория (с подкатегориями)

GET /api/catalog/categories/divany/
Ответ (200 OK):

```
{
  "id": 1,
  "name_ru": "Диваны",
  "name_en": "Sofas",
  "description_ru": "Уютные диваны для вашего дома",
  "description_en": "Cozy sofas for your home",
  "slug": "divany",
  "parent": null,
  "sort_order": 1,
  "is_active": true,
  "children": [
    {
      "id": 3,
      "name_ru": "Угловые диваны",
      "slug": "uglovye-divany",
      "parent": 1
    }
  ],
  "items_count": 15,
  "discounts": []
}
```

### 2.4 Список товаров (с фильтрами)

GET /api/catalog/items/?category=1&is_art=false&ordering=-base_price_rub
Параметры:

    category - фильтр по ID категории

    author - фильтр по ID автора

    is_art - фильтр по типу (true/false)

    is_active - фильтр по активности

    search - поиск по названию и описанию

    ordering - сортировка (created_at, sort_order, base_price_rub, с - для обратного порядка)

    page - номер страницы

    per_page - элементов на странице

Ответ (200 OK):

```
{
  "count": 15,
  "next": "http://api.example.com/catalog/items/?page=2",
  "previous": null,
  "results": [
    {
      "id": 101,
      "name_ru": "Диван Честер",
      "name_en": "Chester Sofa",
      "slug": "divan-chester",
      "category_name": "Диваны",
      "author_name": "Иван Петров",
      "base_price_rub": "89900.00",
      "base_price_usd": "999.00",
      "is_price_hidden": false,
      "preview_photos": ["/media/items/photos/chester_1.jpg"],
      "is_art": false,
      "discount": null,
      "final_price_rub": "89900.00",
      "final_price_usd": "999.00",
      "is_active": true,
      "created_at": "2025-02-19T10:00:00Z"
    }
  ]
}
```

### 2.5 Детальная страница товара

GET /api/catalog/items/divan-chester/
Ответ (200 OK):

```
{
  "id": 101,
  "name_ru": "Диван Честер",
  "name_en": "Chester Sofa",
  "description_ru": "Классический диван в стиле Честерфилд",
  "description_en": "Classic Chesterfield style sofa",
  "slug": "divan-chester",
  "category": {
    "id": 1,
    "name_ru": "Диваны",
    "slug": "divany"
  },
  "author": {
    "id": 5,
    "name_ru": "Иван Петров",
    "slug": "ivan-petrov",
    "photo": "/media/authors/petrov.jpg"
  },
  "is_art": false,
  "is_active": true,
  "base_price_rub": "89900.00",
  "base_price_usd": "999.00",
  "is_price_hidden": false,
  "image_2d": "/media/items/2d/chester_2d.jpg",
  "image_3d": "/media/items/3d/chester.glb",
  "preview_photos": ["/media/items/photos/chester_1.jpg"],
  "photos": [
    "/media/items/photos/chester_1.jpg",
    "/media/items/photos/chester_2.jpg"
  ],
  "sizes": [
    {
      "id": 201,
      "value_ru": "2 места",
      "value_en": "2 seats",
      "price_multiplier": "1.00",
      "is_available": true
    },
    {
      "id": 202,
      "value_ru": "3 места",
      "value_en": "3 seats",
      "price_multiplier": "1.30",
      "is_available": true
    }
  ],
  "specs_by_category": [
    {
      "category": {
        "id": 10,
        "name_ru": "Ткань",
        "name_en": "Fabric"
      },
      "specs": [
        {
          "id": 301,
          "name_ru": "Материал",
          "value_ru": "Велюр",
          "value_en": "Velour",
          "price_modifier_rub": "0.00",
          "price_modifier_usd": "0.00",
          "image": "/media/specs/velour.jpg"
        },
        {
          "id": 302,
          "name_ru": "Материал",
          "value_ru": "Кожа",
          "value_en": "Leather",
          "price_modifier_rub": "15000.00",
          "price_modifier_usd": "150.00",
          "image": "/media/specs/leather.jpg"
        }
      ]
    }
  ],
  "discount": null,
  "final_price_rub": "89900.00",
  "final_price_usd": "999.00",
  "created_at": "2025-02-19T10:00:00Z",
  "updated_at": "2025-02-19T10:00:00Z"
}
```

### 2.6 Характеристики (Specs)

GET /api/catalog/specs/?item=101

Ответ (200 OK):
json
```
[
  {
    "id": 301,
    "name_ru": "Обивка",
    "category_name": "Материал",
    "value_ru": "Велюр",
    "price_modifier_rub": "0.00"
  }
]
```

### 2.7 Размеры

GET /api/catalog/sizes/?item=101

Ответ (200 OK):
json
```
[
  {
    "id": 201,
    "value_ru": "2 места",
    "price_multiplier": "1.00",
    "is_available": true
  }
]
```

### 2.8 Список активных скидок (публичный)

GET /api/catalog/discounts/

Ответ (200 OK):
json
```
[
  {
    "id": 1,
    "name_ru": "Новогодняя распродажа",
    "value": 15,
    "type": "percent",
    "is_active": true
  }
]
```

### 2.9 Детальная информация о скидке

GET /api/catalog/discounts/1/

Ответ (200 OK):
json
```
{
  "id": 1,
  "name_ru": "Новогодняя распродажа",
  "name_en": "New Year Sale",
  "value": 15,
  "type": "percent",
  "valid_from": "2025-12-01T00:00:00Z",
  "valid_to": "2026-01-15T23:59:59Z",
  "is_active": true,
  "categories": [...],
  "items": [...]
}
```

### 2.10 Создание скидки (админ)

POST /api/catalog/discounts/

Headers: Authorization: Bearer <admin_token>

Запрос:
json
```
{
  "name_ru": "Летняя распродажа",
  "value": 20,
  "type": "percent",
  "valid_from": "2026-06-01T00:00:00Z",
  "valid_to": "2026-08-31T23:59:59Z"
}
```
Ответ (201 Created):
json
```
{
  "id": 2,
  "name_ru": "Летняя распродажа",
  "value": 20,
  "type": "percent",
  "is_active": true
}
```

### 2.11 Обновление скидки (админ)

PATCH /api/catalog/discounts/2/

Headers: Authorization: Bearer <admin_token>

Запрос:
json
```
{
  "value": 25
}
```
Ответ (200 OK):
json
```
{
  "id": 2,
  "value": 25
}
```

### 2.12 Удаление скидки (админ)

DELETE /api/catalog/discounts/2/

Headers: Authorization: Bearer <admin_token>

Ответ (204 No Content)



## 3. ИЗБРАННОЕ И MOODBOARD

### 3.1 Добавить товар в избранное

POST /api/favourites/

Headers: Authorization: Bearer <access_token>

Запрос:

```
{
  "item": 101
}
```

Ответ (201 Created):

```
{
  "id": 1,
  "item": {
    "id": 101,
    "name_ru": "Диван Честер",
    "slug": "divan-chester",
    "preview_photos": ["/media/items/photos/chester_1.jpg"],
    "base_price_rub": "89900.00"
  },
  "position": 0,
  "on_moodboard": true,
  "moodboard_position": 0,
  "created_at": "2025-02-19T12:00:00Z"
}
```

### 3.2 Список всех избранных товаров

GET /api/favourites/?page=1&per_page=20
Headers: Authorization: Bearer <access_token>
Ответ (200 OK):

```
{
  "count": 40,
  "total_pages": 2,
  "current_page": 1,
  "per_page": 20,
  "next": "/api/favourites/?page=2&per_page=20",
  "previous": null,
  "results": [
    {
      "id": 1,
      "item": {
        "id": 101,
        "name_ru": "Диван Честер",
        "slug": "divan-chester",
        "preview_photos": ["/media/items/photos/chester_1.jpg"],
        "base_price_rub": "89900.00"
      },
      "position": 0,
      "on_moodboard": true,
      "moodboard_position": 0,
      "created_at": "2025-02-19T12:00:00Z"
    },
    {
      "id": 2,
      "item": {
        "id": 102,
        "name_ru": "Кресло Модерн",
        "slug": "kreslo-modern",
        "preview_photos": ["/media/items/photos/modern_1.jpg"],
        "base_price_rub": "45000.00"
      },
      "position": 1,
      "on_moodboard": false,
      "moodboard_position": 1,
      "created_at": "2025-02-19T12:05:00Z"
    }
    // ... еще 18 элементов
  ]
}
```

### 3.3 Список товаров в Moodboard

GET /api/favourites/moodboard/?page=1&per_page=20

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):

```
{
  "count": 25,
  "total_pages": 2,
  "current_page": 1,
  "per_page": 20,
  "next": "/api/favourites/moodboard/?page=2&per_page=20",
  "previous": null,
  "results": [
    {
      "id": 1,
      "item": {
        "id": 101,
        "name_ru": "Диван Честер",
        "slug": "divan-chester",
        "preview_photos": ["/media/items/photos/chester_1.jpg"],
        "base_price_rub": "89900.00"
      },
      "position": 0,
      "on_moodboard": true,
      "moodboard_position": 0,
      "created_at": "2025-02-19T12:00:00Z"
    }
    // ... еще 19 элементов
  ]
}
```

### 3.4 Переключить видимость в Moodboard (Toggle)

PATCH /api/favourites/{favourite_id}/toggle_moodboard/

Headers: Authorization: Bearer <access_token>
Запрос: {}
Ответ (200 OK):

```
{
  "id": 1,
  "item": {...},
  "position": 0,
  "on_moodboard": false,
  "moodboard_position": 0,
  "created_at": "2025-02-19T12:00:00Z"
}

```

### 3.5 Удалить из избранного полностью

DELETE /api/favourites/1/

Headers: Authorization: Bearer <access_token>

Ответ (204 No Content)

### 3.6 Массовое изменение порядка

POST /api/favourites/reorder/

Headers: Authorization: Bearer <access_token>

Запрос (все избранное):

```
{
  "type": "all",
  "order": [104, 101, 102, 103, 105, 106, 107, 108, 109, 110],
  "page": 1
}
```

Запрос (только Moodboard):

```
{
  "type": "moodboard",
  "order": [115, 117, 112, 113, 114],
  "page": 2
}
```

Ответ (200 OK):

```
{
  "count": 25,
  "total_pages": 3,
  "current_page": 2,
  "per_page": 10,
  "next": "/api/favourites/?page=3&per_page=10",
  "previous": "/api/favourites/?page=1&per_page=10",
  "results": [
    {
      "id": 115,
      "item": {
        "id": 115,
        "name_ru": "Кресло Вега",
        "slug": "kreslo-vega"
      },
      "position": 10,
      "on_moodboard": true,
      "moodboard_position": 10,
      "created_at": "2025-02-19T12:00:00Z"
    },
    {
      "id": 117,
      "item": {
        "id": 117,
        "name_ru": "Стул Омега",
        "slug": "stul-omega"
      },
      "position": 11,
      "on_moodboard": true,
      "moodboard_position": 11,
      "created_at": "2025-02-19T12:05:00Z"
    }
    // ... остальные элементы страницы в новом порядке
  ]
}

```

### 3.7 Получить только ID избранных товаров

GET /api/favourites/ids/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):

```
[101, 102, 105]

```

## 4. КОРЗИНА

### 4.1 Получить корзину

GET /api/cart/
Headers: Authorization: Bearer <access_token>
Ответ (200 OK):

```
{
  "id": 1,
  "items": [
    {
      "id": 1,
      "item": {
        "id": 101,
        "name_ru": "Диван Честер",
        "slug": "divan-chester",
        "preview_photos": ["/media/items/photos/chester_1.jpg"],
        "base_price_rub": "89900.00"
      },
      "size": {
        "id": 202,
        "value_ru": "3 места",
        "price_multiplier": "1.30",
        "is_available": true
      },
      "quantity": 1,
      "selected_specs": [
        {
          "id": 302,
          "name_ru": "Материал",
          "value_ru": "Кожа",
          "price_modifier_rub": "15000.00"
        }
      ],
      "price_rub": "131870.00",
      "price_usd": "1448.70",
      "subtotal_rub": "131870.00",
      "subtotal_usd": "1448.70",
      "added_at": "2025-02-19T13:00:00Z"
    }
  ],
  "total_items": 1,
  "total_price_rub": "131870.00",
  "total_price_usd": "1448.70",
  "created_at": "2025-02-19T13:00:00Z",
  "updated_at": "2025-02-19T13:00:00Z"
}
```

### 4.2 Добавить товар в корзину

POST /api/cart/items/
Headers: Authorization: Bearer <access_token>
Запрос:

```
{
  "item": 101,
  "size_id": 202,
  "spec_ids": [302],
  "quantity": 1
}
```

Ответ (201 Created):

```
{
  "id": 1,
  "item": {...},
  "size": {...},
  "quantity": 1,
  "selected_specs": [...],
  "price_rub": "131870.00",
  "subtotal_rub": "131870.00",
  "added_at": "2025-02-19T13:00:00Z"
}
```

⚠️ Если товар с такими же параметрами уже есть — количество увеличится.

### 4.3 Обновить количество товара

PATCH /api/cart/items/1/

Headers: Authorization: Bearer <access_token>
Запрос:

```
{
  "quantity": 2
}
```

Ответ (200 OK):

```
{
  "id": 1,
  "quantity": 2,
  "subtotal_rub": "263740.00"
}
```

### 4.4 Удалить товар из корзины

DELETE /api/cart/items/1/

Headers: Authorization: Bearer <access_token>

Ответ (204 No Content)
4.5 Очистить корзину

DELETE /api/cart/clear/

Headers: Authorization: Bearer <access_token>

Ответ (204 No Content):
json

{
"message": "Корзина очищена"
}

### 4.6 Получить количество товаров (для бейджа)

GET /api/cart/count/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):

```
{
  "count": 3
}
```

## 5. АДРЕСА ДОСТАВКИ

### 5.1 Список адресов

GET /api/orders/addresses/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):
json

```
[
  {
    "id": 1,
    "label": "Дом",
    "address": "ул. Пушкина, д. 10",
    "entrance": "1",
    "floor": "5",
    "apartment": "50",
    "comment": "Домофон не работает",
    "has_elevator": true,
    "requires_assemblers": false,
    "is_default": true,
    "full_address": "ул. Пушкина, д. 10, подъезд 1, этаж 5, кв/офис 50 (Домофон не работает)",
    "created_at": "2025-02-19T10:00:00Z"
  }
]
```

### 5.2 Добавить адрес

POST /api/orders/addresses/

Headers: Authorization: Bearer <access_token>

Запрос:

```
{
  "label": "Работа",
  "address": "ул. Ленина, д. 5",
  "entrance": "2",
  "floor": "3",
  "apartment": "301",
  "comment": "Звонить за 30 минут",
  "has_elevator": true,
  "requires_assemblers": false,
  "is_default": false
}
```

Ответ (201 Created):

```
{
  "id": 2,
  "label": "Работа",
  "address": "ул. Ленина, д. 5",
  "is_default": false,
  "full_address": "ул. Ленина, д. 5, подъезд 2, этаж 3, кв/офис 301 (Звонить за 30 минут)"
}
```

### 5.3 Обновить адрес

PATCH /api/orders/addresses/1/

Headers: Authorization: Bearer <access_token>

Запрос:

```
{
  "is_default": true
}
```

Ответ (200 OK):

```
{
  "id": 1,
  "label": "Дом",
  "is_default": true
}
```

⚠️ При установке is_default=true остальные адреса автоматически сбрасываются в False

## 6. ПРОМОКОДЫ

### 6.1 Проверить промокод

POST /api/orders/promocodes/validate/

Запрос:
json

```
{
  "code": "SALE2025"
}
```

Ответ (200 OK) - валидный:
json

```
{
  "code": "SALE2025",
  "discount_percent": 10,
  "discount_amount_rub": "0.00",
  "valid": true
}
```

Ответ (400 Bad Request) - невалидный:
json

```
{
  "code": ["Промокод не найден"]
}
```

## 7. ЗАКАЗЫ

### 7.1 Создать заказ из корзины

POST /api/orders/

Headers: Authorization: Bearer <access_token>

Запрос:
json

```
{
  "delivery_address_id": 1,
  "delivery_instructions": "Звонить за час",
  "delivery_cost_rub": "500.00",
  "delivery_cost_usd": "5.00",
  "email": "ivan@example.com",
  "phone": "+79991234567",
  "full_name": "Иван Петров",
  "payment_method": "card",
  "promo_code": "SALE2025",
  "customer_comment": "Позвоните перед доставкой"
}
```

Ответ (201 Created):
json

```
{
  "id": 1,
  "order_number": "ORD-20250219-1234",
  "user": 1,
  "status": "new",
  "payment_status": "pending",
  "payment_method": "card",
  "delivery_address_info": {
    "id": 1,
    "label": "Дом",
    "address": "ул. Пушкина, д. 10",
    "is_default": true
  },
  "delivery_cost_rub": "500.00",
  "delivery_cost_usd": "5.00",
  "subtotal_rub": "131870.00",
  "subtotal_usd": "1448.70",
  "discount_rub": "13187.00",
  "discount_usd": "144.87",
  "total_rub": "119183.00",
  "total_usd": "1308.83",
  "promo_code_text": "SALE2025",
  "customer_comment": "Позвоните перед доставкой",
  "items": [
    {
      "id": 1,
      "item": {...},
      "name": "Диван Честер",
      "sku": "CHS-001",
      "size_value_ru": "3 места",
      "quantity": 1,
      "price_rub": "131870.00",
      "total_rub": "131870.00"
    }
  ],
  "can_cancel": true,
  "can_refund": false,
  "created_at": "2025-02-19T14:00:00Z",
  "paid_at": null
}
```

⚠️ После успешного создания заказа корзина автоматически очищается.

### 7.2 Список заказов пользователя

GET /api/orders/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):
json

```
[
  {
    "id": 1,
    "order_number": "ORD-20250219-1234",
    "status": "new",
    "payment_status": "pending",
    "total_rub": "119183.00",
    "total_usd": "1308.83",
    "items_count": 1,
    "created_at": "2025-02-19T14:00:00Z"
  }
]
```

### 7.3 Детали заказа

GET /api/orders/1/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):
json

```
{
  "id": 1,
  "order_number": "ORD-20250219-1234",
  "user": 1,
  "status": "confirmed",
  "payment_status": "paid",
  "payment_method": "card",
  "delivery_address_info": {...},
  "subtotal_rub": "131870.00",
  "discount_rub": "13187.00",
  "total_rub": "119183.00",
  "items": [...],
  "can_cancel": false,
  "can_refund": true,
  "created_at": "2025-02-19T14:00:00Z",
  "paid_at": "2025-02-19T14:05:00Z"
}
```

### 7.4 Отмена заказа

POST /api/orders/1/cancel/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):
json

```
{
  "id": 1,
  "order_number": "ORD-20250219-1234",
  "status": "cancelled",
  "...": "..."
}
```

Ответ (400 Bad Request) — нельзя отменить:
json

```
{
  "error": "Заказ нельзя отменить"
}
```

### 7.5 Товары в заказе

GET /api/orders/1/items/

Headers: Authorization: Bearer <access_token>

Ответ (200 OK):
json

```
[
  {
    "id": 1,
    "item": {...},
    "name": "Диван Честер",
    "sku": "CHS-001",
    "size_value_ru": "3 места",
    "quantity": 1,
    "price_rub": "131870.00",
    "total_rub": "131870.00",
    "specs_snapshot": {...},
    "image": "/media/items/photos/chester_1.jpg"
  }
]
```

## 8. УСЛУГИ

### 8.1 Список услуг

GET /api/catalog/services/

Ответ (200 OK):
json

```
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name_ru": "Сборка мебели",
      "name_en": "Furniture assembly",
      "slug": "sborka-mebeli",
      "short_description_ru": "Профессиональная сборка мебели на дому",
      "short_description_en": "Professional furniture assembly at home",
      "preview_photos": ["/media/services/assembly.jpg"],
      "price_rub": "5000.00",
      "price_usd": "55.00",
      "is_price_hidden": false,
      "is_active": true,
      "created_at": "2025-02-19T10:00:00Z"
    },
    {
      "id": 2,
      "name_ru": "Доставка",
      "name_en": "Delivery",
      "slug": "dostavka",
      "short_description_ru": "Доставка по городу",
      "short_description_en": "City delivery",
      "preview_photos": ["/media/services/delivery.jpg"],
      "price_rub": "1000.00",
      "price_usd": "11.00",
      "is_price_hidden": false,
      "is_active": true,
      "created_at": "2025-02-19T10:00:00Z"
    }
  ]
}
```

### 8.2 Детальная страница услуги

GET /api/catalog/services/sborka-mebeli/

Ответ (200 OK):
json

```
{
  "id": 1,
  "name_ru": "Сборка мебели",
  "name_en": "Furniture assembly",
  "description_ru": "Мы предлагаем профессиональную сборку мебели с гарантией качества. Наши мастера имеют многолетний опыт работы с мебелью любых производителей.",
  "description_en": "We offer professional furniture assembly with quality guarantee. Our craftsmen have many years of experience working with furniture from any manufacturer.",
  "short_description_ru": "Профессиональная сборка мебели на дому",
  "short_description_en": "Professional furniture assembly at home",
  "slug": "sborka-mebeli",
  "preview_photos": ["/media/services/assembly_preview.jpg"],
  "photos": [
    "/media/services/assembly_1.jpg",
    "/media/services/assembly_2.jpg"
  ],
  "sort_order": 1,
  "price_rub": "5000.00",
  "price_usd": "55.00",
  "is_price_hidden": false,
  "discounts": [
    {
      "id": 1,
      "name_ru": "Сезонная скидка",
      "value": 10,
      "type": "percent",
      "is_active": true
    }
  ],
  "is_active": true,
  "created_at": "2025-02-19T10:00:00Z",
  "updated_at": "2025-02-19T10:00:00Z"
}
```

## 9. ГЛОБАЛЬНЫЙ ПОИСК

### 9.1 Поиск по всем разделам

GET /api/catalog/search/?q=диван

Параметры:

    q - поисковый запрос (минимум 2 символа)

Ответ (200 OK):
json

```
{
  "items": [
    {
      "id": 1,
      "name_ru": "Диван Честер",
      "slug": "divan-chester",
      "category_name": "Диваны",
      "base_price_rub": "89900.00",
      "preview_photos": ["/media/items/chester.jpg"]
    }
  ],
  "categories": [
    {
      "id": 1,
      "name_ru": "Диваны",
      "slug": "divany",
      "items_count": 15
    }
  ],
  "authors": [
    {
      "id": 1,
      "name_ru": "Иван Петров",
      "slug": "ivan-petrov"
    }
  ],
  "services": [
    {
      "id": 1,
      "name_ru": "Сборка мебели",
      "slug": "sborka-mebeli",
      "price_rub": "5000.00"
    }
  ]
}
```

## 10. КОДЫ ОТВЕТОВ

Код Описание
200 OK - успешный запрос
201 Created - ресурс создан
204 No Content - успешное удаление
400 Bad Request - неверные параметры
401 Unauthorized - требуется авторизация
403 Forbidden - недостаточно прав
404 Not Found - ресурс не найден
429 Too Many Requests - слишком много запросов

## 11. ПАГИНАЦИЯ

Все списковые эндпоинты поддерживают пагинацию с параметрами:

    page - номер страницы (по умолчанию 1)

    per_page - элементов на странице (по умолчанию 20, макс. 100)

Формат ответа с пагинацией:
json

```
{
  "count": 150,
  "total_pages": 8,
  "current_page": 1,
  "per_page": 20,
  "has_is_main": true,  // только для блога
  "next": "http://127.0.0.1:8000/api/catalog/items/?page=2",
  "previous": null,
  "results": [...]
}
```
