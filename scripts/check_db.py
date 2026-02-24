#!/usr/bin/env python
import os
import sys
import sqlite3
from pathlib import Path

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_database():
    """Проверяет состояние базы данных"""

    from django.conf import settings

    db_path = settings.DATABASES['default']['NAME']

    print("=" * 60)
    print(" ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    print(f" Путь к БД: {db_path}")

    if not os.path.exists(db_path):
        print(" Файл базы данных НЕ СУЩЕСТВУЕТ")
        return False

    # Размер файла
    size = os.path.getsize(db_path)
    if size < 1024:
        size_display = f"{size} B"
    elif size < 1024 * 1024:
        size_display = f"{size / 1024:.2f} KB"
    else:
        size_display = f"{size / (1024 * 1024):.2f} MB"

    print(f" Файл существует")
    print(f" Размер: {size_display}")

    # Проверяем целостность SQLite
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f" Таблиц в базе: {len(tables)}")

        # Проверяем несколько ключевых таблиц
        important_tables = [
            'auth_user',
            'core_conferenceinfo',
            'talks_report',
            'users_user'
        ]

        for table in important_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    {table}: {count} записей")
            else:
                print(f"    {table}: не найдена")

        conn.close()
        print(" База данных в порядке")
        return True

    except Exception as e:
        print(f" Ошибка при проверке БД: {e}")
        return False


if __name__ == '__main__':
    check_database()