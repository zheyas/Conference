#!/usr/bin/env python
import os
import sys
import django
import time

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conference.settings')

# Ждем немного, чтобы база данных успела инициализироваться
time.sleep(2)

try:
    django.setup()
except Exception as e:
    print(f"❌ Ошибка при настройке Django: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

User = get_user_model()


def create_superuser_from_env():
    """Создает суперпользователя из переменных окружения"""

    # Берем данные из .env
    email = os.getenv('SUPERUSER_EMAIL')
    password = os.getenv('SUPERUSER_PASSWORD')
    first_name = os.getenv('SUPERUSER_FIRST_NAME', 'Admin')
    last_name = os.getenv('SUPERUSER_LAST_NAME', 'User')

    if not email or not password:
        print("❌ SUPERUSER_EMAIL или SUPERUSER_PASSWORD не заданы в .env")
        return False

    try:
        # Проверяем, существует ли пользователь
        if User.objects.filter(email=email).exists():
            print(f"✅ Суперпользователь {email} уже существует")
            return True

        # Создаем суперпользователя
        User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='super_admin'
        )

        print(f"✅ Суперпользователь успешно создан:")
        print(f"   Email: {email}")
        print(f"   Имя: {first_name} {last_name}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при создании суперпользователя: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🔧 СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ ИЗ .ENV")
    print("=" * 60)

    success = create_superuser_from_env()

    if success:
        print("=" * 60)
        print("✅ ГОТОВО")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ ОШИБКА")
        print("=" * 60)
        sys.exit(1)