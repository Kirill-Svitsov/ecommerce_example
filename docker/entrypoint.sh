#!/bin/sh

# Применяем миграции
python3 manage.py migrate --noinput

# Собираем статику
python3 manage.py collectstatic --noinput

# Компилируем переводы
python3 manage.py compilemessages

# Запускаем сервер
exec "$@"
