#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conference.settings')  # замените на имя вашего проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from users.models import User


def create_test_users():
    """Создание тестовых пользователей"""

    # Удаляем существующих тестовых пользователей (по email)
    test_emails = [
        'admin@conference.ru',
        'moderator@conference.ru',
        'reviewer1@conference.ru',
        'reviewer2@conference.ru',
        'chairman1@conference.ru',
        'chairman2@conference.ru',
        'jury1@conference.ru',
        'jury2@conference.ru',
        'user1@conference.ru',
        'user2@conference.ru',
        'user3@conference.ru',
    ]

    User.objects.filter(email__in=test_emails).delete()

    # Пароль для всех тестовых пользователей
    password = 'testpass123'

    # 1. Супер-администратор
    super_admin = User.objects.create_superuser(
        email='admin@conference.ru',
        password=password,
        first_name='Иван',
        last_name='Петров',
        middle_name='Сергеевич',
        organization='Организационный комитет',
        position='Руководитель',
        academic_degree='Доктор наук',
        academic_title='Профессор',
        role='super_admin'
    )

    # 2. Администратор конференции
    admin = User.objects.create_user(
        email='admin2@conference.ru',
        password=password,
        first_name='Анна',
        last_name='Сидорова',
        middle_name='Ивановна',
        organization='Организационный комитет',
        position='Администратор',
        role='admin'
    )

    # 3. Модератор
    moderator = User.objects.create_user(
        email='moderator@conference.ru',
        password=password,
        first_name='Михаил',
        last_name='Кузнецов',
        middle_name='Александрович',
        organization='Программный комитет',
        position='Модератор',
        role='moderator'
    )

    # 4. Рецензенты
    reviewer1 = User.objects.create_user(
        email='reviewer1@conference.ru',
        password=password,
        first_name='Ольга',
        last_name='Николаева',
        middle_name='Викторовна',
        organization='МГУ им. Ломоносова',
        position='Доцент',
        academic_degree='Кандидат наук',
        role='reviewer'
    )

    reviewer2 = User.objects.create_user(
        email='reviewer2@conference.ru',
        password=password,
        first_name='Алексей',
        last_name='Федоров',
        middle_name='Петрович',
        organization='СПбГУ',
        position='Профессор',
        academic_degree='Доктор наук',
        role='reviewer'
    )

    # 5. Председатели жюри
    chairman1 = User.objects.create_user(
        email='chairman1@conference.ru',
        password=password,
        first_name='Сергей',
        last_name='Волков',
        middle_name='Дмитриевич',
        organization='ИТМО',
        position='Профессор',
        academic_degree='Доктор наук',
        role='reviewer'  # или можно оставить как 'user'
    )

    chairman2 = User.objects.create_user(
        email='chairman2@conference.ru',
        password=password,
        first_name='Елена',
        last_name='Морозова',
        middle_name='Анатольевна',
        organization='ВШЭ',
        position='Профессор',
        academic_degree='Доктор наук',
        role='reviewer'
    )

    # 6. Члены жюри
    jury1 = User.objects.create_user(
        email='jury1@conference.ru',
        password=password,
        first_name='Дмитрий',
        last_name='Соколов',
        middle_name='Игоревич',
        organization='МИФИ',
        position='Доцент',
        academic_degree='Кандидат наук',
        role='reviewer'
    )

    jury2 = User.objects.create_user(
        email='jury2@conference.ru',
        password=password,
        first_name='Марина',
        last_name='Павлова',
        middle_name='Сергеевна',
        organization='МФТИ',
        position='Старший научный сотрудник',
        academic_degree='Кандидат наук',
        role='reviewer'
    )

    # 7. Обычные пользователи
    user1 = User.objects.create_user(
        email='user1@conference.ru',
        password=password,
        first_name='Андрей',
        last_name='Иванов',
        middle_name='Павлович',
        organization='Университет инноваций',
        position='Аспирант',
        role='user'
    )

    user2 = User.objects.create_user(
        email='user2@conference.ru',
        password=password,
        first_name='Наталья',
        last_name='Ковалева',
        middle_name='Александровна',
        organization='Технический университет',
        position='Магистрант',
        role='user'
    )

    user3 = User.objects.create_user(
        email='user3@conference.ru',
        password=password,
        first_name='Артем',
        last_name='Белов',
        middle_name='Владимирович',
        organization='Научный центр',
        position='Исследователь',
        role='user'
    )

    # Выводим логины и пароли
    print("=" * 50)
    print("ТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ СОЗДАНЫ")
    print("=" * 50)
    print()
    print("Логин (email)                 | Пароль      | Роль")
    print("-" * 50)

    users = [
        (super_admin.email, password, "Супер-администратор"),
        (admin.email, password, "Администратор"),
        (moderator.email, password, "Модератор"),
        (reviewer1.email, password, "Рецензент 1"),
        (reviewer2.email, password, "Рецензент 2"),
        (chairman1.email, password, "Председатель жюри 1"),
        (chairman2.email, password, "Председатель жюри 2"),
        (jury1.email, password, "Член жюри 1"),
        (jury2.email, password, "Член жюри 2"),
        (user1.email, password, "Участник 1"),
        (user2.email, password, "Участник 2"),
        (user3.email, password, "Участник 3"),
    ]

    for email, pwd, role in users:
        print(f"{email:<30} | {pwd:<11} | {role}")

    print()
    print("=" * 50)
    print(f"Всего создано: {len(users)} пользователей")
    print("Пароль для всех: testpass123")


if __name__ == '__main__':
    create_test_users()