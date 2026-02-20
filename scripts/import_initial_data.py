#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conference.settings')
django.setup()

from core.models import ConferenceInfo, Contact, Organizer, UsefulLink, ImportantDate
from django.utils import timezone


def import_conference_info():
    """Импорт информации о конференции"""
    print("Импорт информации о конференции...")

    info, created = ConferenceInfo.objects.get_or_create(
        title='IT-Весна 2026',
        defaults={
            'subtitle': 'Студенческая научно-техническая конференция',
            'description': 'Ежегодная студенческая конференция для молодых исследователей и разработчиков в области информационных технологий. Представьте свои проекты, исследования и инновационные идеи научному сообществу.',
            'start_date': date(2026, 5, 15),
            'end_date': date(2026, 5, 17),
            'location': 'Главный корпус ОГУ',
            'submission_deadline': date(2026, 4, 1),
            'notification_date': date(2026, 4, 15),
            'is_active': True
        }
    )

    if created:
        print(f" Создана информация о конференции: {info.title}")
    else:
        print(f" Информация о конференции уже существует: {info.title}")

    return info


def import_contacts():
    """Импорт контактов"""
    print("\nИмпорт контактов...")

    contacts_data = [
        {
            'contact_type': 'email',
            'title': 'Оргкомитет',
            'value': 'conference@osu.ru',
            'icon': 'bi-envelope',
            'order': 1
        },
        {
            'contact_type': 'phone',
            'title': 'Оргкомитет',
            'value': '+7 (3532) 37-24-78',
            'icon': 'bi-telephone',
            'order': 2
        },
        {
            'contact_type': 'address',
            'title': 'Адрес',
            'value': '460018, г. Оренбург, пр. Победы, 13',
            'icon': 'bi-geo-alt',
            'order': 3
        },
        {
            'contact_type': 'other',
            'title': 'Официальный сайт ОГУ',
            'value': 'https://osu.ru',
            'icon': 'bi-globe',
            'order': 4
        }
    ]

    for contact_data in contacts_data:
        contact, created = Contact.objects.get_or_create(
            contact_type=contact_data['contact_type'],
            value=contact_data['value'],
            defaults=contact_data
        )

        if created:
            print(f" Создан контакт: {contact.get_contact_type_display()} - {contact.value}")
        else:
            print(f" Контакт уже существует: {contact.get_contact_type_display()} - {contact.value}")


def import_organizers():
    """Импорт организаторов"""
    print("\nИмпорт организаторов...")

    organizers_data = [
        {
            'name': 'Факультет математики и информационных технологий',
            'description': 'Организатор конференции',
            'order': 1
        },
        {
            'name': 'Студенческое научное общество ОГУ',
            'description': 'Соорганизатор',
            'order': 2
        },
        {
            'name': 'Научно-исследовательская часть ОГУ',
            'description': 'Соорганизатор',
            'order': 3
        }
    ]

    for org_data in organizers_data:
        organizer, created = Organizer.objects.get_or_create(
            name=org_data['name'],
            defaults=org_data
        )

        if created:
            print(f" Создан организатор: {organizer.name}")
        else:
            print(f" Организатор уже существует: {organizer.name}")


def import_useful_links():
    """Импорт полезных ссылок"""
    print("\nИмпорт полезных ссылок...")

    links_data = [
        {
            'title': 'Официальный сайт ОГУ',
            'url': 'https://osu.ru',
            'order': 1
        },
        {
            'title': 'Научная деятельность',
            'url': 'https://osu.ru/science',
            'order': 2
        },
        {
            'title': 'Студенческий портал',
            'url': 'https://osu.ru/students',
            'order': 3
        },
        {
            'title': 'Факультет МИТ',
            'url': 'https://osu.ru/mit',
            'order': 4
        }
    ]

    for link_data in links_data:
        link, created = UsefulLink.objects.get_or_create(
            title=link_data['title'],
            defaults=link_data
        )

        if created:
            print(f" Создана ссылка: {link.title}")
        else:
            print(f"️ Ссылка уже существует: {link.title}")


def import_important_dates():
    """Импорт важных дат"""
    print("\nИмпорт важных дат...")

    dates_data = [
        {
            'title': 'Регистрация участников',
            'date': date(2026, 3, 1),
            'description': 'Начало регистрации участников',
            'order': 1
        },
        {
            'title': 'Закрытие регистрации',
            'date': date(2026, 3, 31),
            'description': 'Окончание регистрации',
            'order': 2
        },
        {
            'title': 'Публикация программы',
            'date': date(2026, 4, 20),
            'description': 'Публикация окончательной программы',
            'order': 3
        }
    ]

    for date_data in dates_data:
        important_date, created = ImportantDate.objects.get_or_create(
            title=date_data['title'],
            date=date_data['date'],
            defaults=date_data
        )

        if created:
            print(f" Создана важная дата: {important_date.title} - {important_date.date}")
        else:
            print(f"️ Важная дата уже существует: {important_date.title} - {important_date.date}")


def main():
    """Главная функция"""
    print("=" * 60)
    print("ИМПОРТ НАЧАЛЬНЫХ ДАННЫХ В CORE ПРИЛОЖЕНИЕ")
    print("=" * 60)

    # Импорт данных
    import_conference_info()
    import_contacts()
    import_organizers()
    import_useful_links()
    import_important_dates()

    print("\n" + "=" * 60)
    print("ИМПОРТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 60)

    # Статистика
    print(f"\nСтатистика:")
    print(f" ConferenceInfo: {ConferenceInfo.objects.count()}")
    print(f" Contacts: {Contact.objects.count()}")
    print(f" Organizers: {Organizer.objects.count()}")
    print(f" UsefulLinks: {UsefulLink.objects.count()}")
    print(f" ImportantDates: {ImportantDate.objects.count()}")

if __name__ == '__main__':
    main()