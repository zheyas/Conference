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


def create_superuser():
    """Создает суперпользователя из переменных окружения если его еще нет"""

    # Берем данные из .env
    email = os.getenv('SUPERUSER_EMAIL')
    password = os.getenv('SUPERUSER_PASSWORD')
    first_name = os.getenv('SUPERUSER_FIRST_NAME', 'Admin')
    last_name = os.getenv('SUPERUSER_LAST_NAME', 'User')

    # Проверяем, что email и password заданы
    if not email or not password:
        print("⚠️ SUPERUSER_EMAIL или SUPERUSER_PASSWORD не заданы, пропускаем создание суперпользователя")
        return True

    try:
        # Проверяем, существует ли уже пользователь
        if User.objects.filter(email=email).exists():
            print(f"✅ Суперпользователь {email} уже существует")
            return True

        # Создаем суперпользователя
        superuser = User.objects.create_superuser(
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


def create_initial_data():
    """Создает начальные данные для приложения core"""
    try:
        from core.models import ConferenceInfo, Contact, Organizer, UsefulLink
        from datetime import date

        # Создаем информацию о конференции если нет
        if not ConferenceInfo.objects.exists():
            ConferenceInfo.objects.create(
                title='IT-Весна 2026',
                subtitle='Студенческая научно-техническая конференция',
                description='Ежегодная студенческая конференция для молодых исследователей и разработчиков в области информационных технологий.',
                start_date=date(2026, 5, 15),
                end_date=date(2026, 5, 17),
                location='Главный корпус ОГУ',
                submission_deadline=date(2026, 4, 1),
                notification_date=date(2026, 4, 15),
                is_active=True
            )
            print("✅ Создана информация о конференции")

        # Создаем контакты если нет
        if not Contact.objects.exists():
            contacts_data = [
                {'contact_type': 'email', 'title': 'Оргкомитет', 'value': 'conference@osu.ru', 'icon_type': 'bootstrap',
                 'icon_bootstrap': 'bi-envelope', 'order': 1},
                {'contact_type': 'phone', 'title': 'Оргкомитет', 'value': '+7 (3532) 37-24-78',
                 'icon_type': 'bootstrap', 'icon_bootstrap': 'bi-telephone', 'order': 2},
                {'contact_type': 'address', 'title': 'Адрес', 'value': '460018, г. Оренбург, пр. Победы, 13',
                 'icon_type': 'bootstrap', 'icon_bootstrap': 'bi-geo-alt', 'order': 3},
                {'contact_type': 'other', 'title': 'Официальный сайт ОГУ', 'value': 'https://osu.ru',
                 'icon_type': 'bootstrap', 'icon_bootstrap': 'bi-globe', 'order': 4},
            ]

            for data in contacts_data:
                Contact.objects.create(**data)
            print("✅ Созданы контакты")

        # Создаем организаторов если нет
        if not Organizer.objects.exists():
            organizers_data = [
                {'name': 'Факультет математики и информационных технологий', 'order': 1, 'icon_type': 'bootstrap',
                 'icon_bootstrap': 'bi-building'},
                {'name': 'Студенческое научное общество ОГУ', 'order': 2, 'icon_type': 'bootstrap',
                 'icon_bootstrap': 'bi-people'},
                {'name': 'Научно-исследовательская часть ОГУ', 'order': 3, 'icon_type': 'bootstrap',
                 'icon_bootstrap': 'bi-flask'},
            ]

            for data in organizers_data:
                Organizer.objects.create(**data)
            print("✅ Созданы организаторы")

        # Создаем полезные ссылки если нет
        if not UsefulLink.objects.exists():
            links_data = [
                {'title': 'Официальный сайт ОГУ', 'url': 'https://osu.ru', 'order': 1},
                {'title': 'Научная деятельность', 'url': 'https://osu.ru/science', 'order': 2},
                {'title': 'Студенческий портал', 'url': 'https://osu.ru/students', 'order': 3},
                {'title': 'Факультет МИТ', 'url': 'https://osu.ru/mit', 'order': 4},
            ]

            for data in links_data:
                UsefulLink.objects.create(**data)
            print("✅ Созданы полезные ссылки")

        return True

    except Exception as e:
        print(f"❌ Ошибка при создании начальных данных: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🔧 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("=" * 60)

    create_superuser()
    create_initial_data()

    print("=" * 60)
    print("✅ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)