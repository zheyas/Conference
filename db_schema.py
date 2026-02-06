#!/usr/bin/env python3
# /Users/evgenijasakov/QuasWexExort/db_schema.py
"""
Инспектор базы данных Supabase - показывает все таблицы и данные
Использует только публичный API без доступа к системным таблицам
"""

import os
import sys
from supabase import create_client, Client
from tabulate import tabulate
from typing import List, Tuple, Dict, Any, Optional
import json
import re


class SupabaseInspector:
    def __init__(self, url: str = None, key: str = None):
        """Инициализация подключения к Supabase"""
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        self.supabase: Client = None
        self.discovered_tables = []

    def connect(self) -> bool:
        """Подключение к Supabase"""
        try:
            if not self.url or not self.key:
                print("❌ Не указаны Supabase URL и KEY")
                print("Укажите через параметры или установите переменные окружения:")
                print("  SUPABASE_URL=https://your-project.supabase.co")
                print("  SUPABASE_KEY=your-anon-key")
                return False

            print(f"Подключаюсь к Supabase: {self.url}")
            self.supabase = create_client(self.url, self.key)

            # Простая проверка подключения
            try:
                # Пробуем получить информацию о проекте
                response = self.supabase.table('profiles').select('id').limit(1).execute()
                print("✅ Подключение к Supabase успешно!")
            except:
                # Даже если таблицы нет, соединение установлено
                print("✅ Подключение установлено (но таблица profiles не найдена)")

            return True

        except Exception as e:
            print(f"❌ Ошибка подключения к Supabase: {e}")
            return False

    def print_header(self, title: str):
        """Печать заголовка"""
        print("\n" + "=" * 80)
        print(f" {title} ".center(80, "="))
        print("=" * 80)

    def discover_tables(self) -> List[str]:
        """Обнаружение таблиц путем попыток доступа к распространенным именам"""
        if self.discovered_tables:
            return self.discovered_tables

        common_table_patterns = [
            # Пользователи и профили
            'users', 'user', 'profiles', 'profile', 'accounts', 'account',
            'auth_users', 'auth_user',

            # Контент и данные
            'todos', 'todo', 'tasks', 'task', 'notes', 'note',
            'posts', 'post', 'articles', 'article', 'blogs', 'blog',
            'comments', 'comment', 'reviews', 'review',
            'products', 'product', 'items', 'item', 'goods',
            'orders', 'order', 'purchases', 'purchase',
            'categories', 'category', 'tags', 'tag',
            'messages', 'message', 'chats', 'chat',

            # Настройки и системное
            'settings', 'setting', 'configs', 'config',
            'files', 'file', 'uploads', 'upload',
            'logs', 'log', 'events', 'event',

            # Django-подобные таблицы
            'django_migrations', 'django_content_type', 'django_admin_log',
            'django_session', 'auth_group', 'auth_permission',
            'auth_user', 'auth_user_groups', 'auth_user_user_permissions',

            # Конференции
            'talks', 'talk', 'presentations', 'presentation',
            'conferences', 'conference', 'sessions', 'session',
            'speakers', 'speaker', 'attendees', 'attendee',
            'tracks', 'track', 'schedules', 'schedule',
            'submissions', 'submission', 'reviews', 'review'
        ]

        discovered = []

        print("🔍 Поиск таблиц в базе данных...")

        for table in common_table_patterns:
            try:
                # Пробуем получить одну запись
                response = self.supabase.table(table).select('*').limit(1).execute()

                # Проверяем, есть ли данные или хотя бы структура доступна
                if hasattr(response, 'data'):
                    discovered.append(table)
                    print(f"  ✅ Найдена таблица: {table}")

            except Exception as e:
                # Игнорируем ошибки "таблица не найдена"
                error_msg = str(e).lower()
                if 'not found' not in error_msg and 'does not exist' not in error_msg:
                    # Другие ошибки могут указывать на существование таблицы
                    # но с проблемами доступа
                    pass

        # Также пробуем найти таблицы через RPC если доступно
        try:
            # Пробуем вызвать простую RPC функцию
            test_rpc = self.supabase.rpc('hello_world', {}).execute()
            if hasattr(test_rpc, 'data'):
                print("  ℹ️ RPC функции доступны")
        except:
            pass

        self.discovered_tables = discovered
        return discovered

    def get_table_schema_by_example(self, table_name: str) -> List[Dict]:
        """Получить схему таблицы на основе примера данных"""
        try:
            # Получаем несколько записей для анализа структуры
            response = self.supabase.table(table_name).select('*').limit(5).execute()

            if hasattr(response, 'data') and response.data:
                # Анализируем первую запись для определения типов
                first_row = response.data[0]
                schema = []

                for column, value in first_row.items():
                    if value is None:
                        data_type = 'unknown'
                    elif isinstance(value, str):
                        data_type = 'text'
                    elif isinstance(value, (int, float)):
                        data_type = 'numeric'
                    elif isinstance(value, bool):
                        data_type = 'boolean'
                    elif isinstance(value, dict):
                        data_type = 'jsonb'
                    elif isinstance(value, list):
                        data_type = 'array'
                    else:
                        data_type = str(type(value))

                    schema.append({
                        'column_name': column,
                        'data_type': data_type,
                        'example_value': str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                    })

                return schema
            else:
                return []

        except Exception as e:
            print(f"⚠️ Не удалось получить схему таблицы {table_name}: {e}")
            return []

    def get_table_data(self, table_name: str, limit: int = 10) -> Tuple[List[str], List[Dict]]:
        """Получить данные из таблицы"""
        try:
            response = self.supabase.table(table_name).select('*').limit(limit).execute()

            if hasattr(response, 'data') and response.data:
                # Получаем названия столбцов из первой записи
                columns = list(response.data[0].keys())
                # Получаем данные
                rows = response.data
                return columns, rows
            else:
                return [], []

        except Exception as e:
            print(f"⚠️ Не удалось получить данные из таблицы {table_name}: {e}")
            return [], []

    def get_table_row_count(self, table_name: str) -> int:
        """Получить количество строк в таблице"""
        try:
            # Используем count API
            response = self.supabase.table(table_name).select('*', count='exact').limit(1).execute()

            if hasattr(response, 'count'):
                return response.count
            elif hasattr(response, 'data'):
                # Если count не доступен, попробуем оценить
                response = self.supabase.table(table_name).select('*').limit(100).execute()
                if hasattr(response, 'data'):
                    # Возвращаем точное количество, если записей <= 100
                    return len(response.data)
            return 0

        except Exception as e:
            print(f"⚠️ Не удалось получить количество записей в {table_name}: {e}")
            return 0

    def get_database_info(self) -> Dict[str, Any]:
        """Получить информацию о базе данных"""
        info = {
            'url': self.url,
            'project_id': self.url.split('.')[0].replace('https://', '') if self.url else '',
            'tables_count': 0
        }

        try:
            tables = self.discover_tables()
            info['tables_count'] = len(tables)
            info['tables'] = tables

        except Exception as e:
            print(f"⚠️ Не удалось получить информацию о БД: {e}")

        return info

    def print_database_info(self):
        """Вывести информацию о базе данных"""
        self.print_header("ИНФОРМАЦИЯ О SUPABASE ПРОЕКТЕ")

        info = self.get_database_info()

        print(f"🌐 URL проекта: {info['url']}")
        print(f"🔑 Project ID: {info['project_id']}")
        print(f"📊 Обнаружено таблиц: {info['tables_count']}")

        if info['tables_count'] > 0:
            print(f"📋 Таблицы: {', '.join(info['tables'][:10])}")
            if len(info['tables']) > 10:
                print(f"  ... и еще {len(info['tables']) - 10} таблиц")

    def print_all_tables(self):
        """Вывести список всех таблиц"""
        self.print_header("СПИСОК ОБНАРУЖЕННЫХ ТАБЛИЦ")

        tables = self.discover_tables()

        if not tables:
            print("❌ Не удалось обнаружить таблицы в базе данных!")
            print("\nВозможные причины:")
            print("  1. База данных пустая")
            print("  2. Таблицы имеют нестандартные имена")
            print("  3. Нет прав на чтение таблиц")
            print("  4. Все таблицы в других схемах (не public)")

            print("\n🔄 Попробуйте ввести названия таблиц вручную...")
            manual_tables = input("Введите названия таблиц через запятую (или нажмите Enter): ").strip()
            if manual_tables:
                tables = [t.strip() for t in manual_tables.split(',')]
                self.discovered_tables.extend(tables)

            if not tables:
                return

        print(f"Всего обнаружено таблиц: {len(tables)}")

        # Группируем таблицы по типам
        user_tables = [t for t in tables if 'user' in t.lower() or 'profile' in t.lower() or 'account' in t.lower()]
        content_tables = [t for t in tables if
                          any(word in t.lower() for word in ['post', 'article', 'blog', 'comment', 'product', 'order'])]
        system_tables = [t for t in tables if t.startswith('django_') or t.startswith('auth_')]
        other_tables = [t for t in tables if
                        t not in user_tables and t not in content_tables and t not in system_tables]

        if user_tables:
            print("\n👥 Таблицы пользователей:")
            for i, table in enumerate(user_tables, 1):
                count = self.get_table_row_count(table)
                print(f"  {i:2}. {table:<25} [≈{count} записей]")

        if content_tables:
            print("\n📝 Контентные таблицы:")
            for i, table in enumerate(content_tables, 1):
                count = self.get_table_row_count(table)
                print(f"  {i:2}. {table:<25} [≈{count} записей]")

        if system_tables:
            print("\n⚙️ Системные таблицы:")
            for i, table in enumerate(system_tables, 1):
                count = self.get_table_row_count(table)
                print(f"  {i:2}. {table:<25} [≈{count} записей]")

        if other_tables:
            print("\n📊 Другие таблицы:")
            for i, table in enumerate(other_tables, 1):
                count = self.get_table_row_count(table)
                print(f"  {i:2}. {table:<25} [≈{count} записей]")

    def print_table_details(self, table_name: str, show_data: bool = True, data_limit: int = 5):
        """Вывести детальную информацию о таблице"""
        self.print_header(f"ТАБЛИЦА: {table_name}")

        # Схема таблицы
        schema = self.get_table_schema_by_example(table_name)

        if schema:
            print("📐 СТРУКТУРА ТАБЛИЦЫ (определено по данным):")
            headers = ["Поле", "Предполагаемый тип", "Пример значения"]
            table_data = [[col['column_name'], col['data_type'], col['example_value']]
                          for col in schema]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            print("⚠️ Не удалось определить структуру таблицы")

        # Количество строк
        row_count = self.get_table_row_count(table_name)
        print(f"\n📊 Примерное количество записей: {row_count}")

        # Данные таблицы
        if show_data and row_count > 0:
            print(f"\n📋 ДАННЫЕ (первые {data_limit} записей):")
            columns, rows = self.get_table_data(table_name, data_limit)

            if rows:
                # Форматируем данные для отображения
                formatted_rows = []
                for row in rows:
                    formatted_row = []
                    for col in columns:
                        value = row.get(col)
                        if value is None:
                            formatted_row.append("NULL")
                        elif isinstance(value, str) and len(value) > 30:
                            formatted_row.append(value[:27] + "...")
                        elif isinstance(value, dict):
                            formatted_row.append(json.dumps(value, ensure_ascii=False)[:30] + "...")
                        elif isinstance(value, list):
                            formatted_row.append(f"[список из {len(value)} элементов]")
                        else:
                            formatted_row.append(str(value))
                    formatted_rows.append(formatted_row)

                print(tabulate(formatted_rows, headers=columns, tablefmt="grid"))

                if row_count > data_limit:
                    print(f"\n⚠️ Показано только {data_limit} из ~{row_count} записей")
            else:
                print("⚠️ Не удалось получить данные таблицы")

    def print_table_statistics(self):
        """Вывести статистику по таблицам"""
        self.print_header("СТАТИСТИКА ТАБЛИЦ")

        tables = self.discover_tables()
        if not tables:
            print("❌ Не обнаружено таблиц")
            return

        statistics = []
        total_rows = 0

        for table in tables:
            row_count = self.get_table_row_count(table)
            total_rows += row_count
            statistics.append([table, row_count])

        # Сортируем по количеству записей
        statistics.sort(key=lambda x: x[1], reverse=True)

        headers = ["Таблица", "Примерное количество записей"]
        print(tabulate(statistics, headers=headers, tablefmt="grid"))
        print(f"\n📈 Всего записей во всех таблицах: ~{total_rows}")

        # Гистограмма
        if statistics:
            print("\n📊 ГИСТОГРАММА (масштаб 1 🟩 = 10 записей):")
            max_rows = max(row_count for _, row_count in statistics) if statistics else 0

            for table, row_count in statistics:
                if max_rows > 0:
                    bar_length = int((row_count / max_rows) * 50)
                else:
                    bar_length = 0

                bar = "🟩" * (bar_length // 10) + "⬜" * (5 - bar_length // 10)
                print(f"  {table:<25} {bar} ~{row_count}")

    def execute_custom_query(self, table_name: str = None):
        """Выполнить пользовательский запрос к таблице"""
        if not table_name:
            tables = self.discover_tables()
            if not tables:
                print("❌ Нет доступных таблиц")
                return

            print("\nДоступные таблицы:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")

            try:
                choice = int(input("\nВыберите таблицу (номер): ")) - 1
                if 0 <= choice < len(tables):
                    table_name = tables[choice]
                else:
                    print("❌ Неверный выбор")
                    return
            except:
                print("❌ Неверный ввод")
                return

        while True:
            print(f"\n📝 Запросы к таблице: {table_name}")
            print("  1. Выбрать все записи")
            print("  2. Выбрать определенные столбцы")
            print("  3. Фильтровать по значению")
            print("  4. Сортировать")
            print("  5. Показать структуру таблицы")
            print("  0. Назад")

            choice = input("\nВыберите действие (0-5): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                try:
                    limit = int(input("Лимит записей (1-100): "))
                    limit = max(1, min(100, limit))
                    self._select_all(table_name, limit)
                except:
                    print("❌ Неверный ввод")
            elif choice == "2":
                columns = input("Столбцы через запятую (например: id,name,email): ").strip()
                if columns:
                    self._select_columns(table_name, columns)
            elif choice == "3":
                column = input("Столбец для фильтрации: ").strip()
                value = input("Значение: ").strip()
                operator = input("Оператор (=, !=, >, <, >=, <=, like) [=]: ").strip() or "="
                if column and value:
                    self._filter_table(table_name, column, value, operator)
            elif choice == "4":
                column = input("Столбец для сортировки: ").strip()
                order = input("Порядок (asc/desc) [asc]: ").strip() or "asc"
                if column:
                    self._sort_table(table_name, column, order)
            elif choice == "5":
                self.print_table_details(table_name, show_data=False)

    def _select_all(self, table_name: str, limit: int = 10):
        """Выбрать все записи"""
        try:
            response = self.supabase.table(table_name).select('*').limit(limit).execute()

            if hasattr(response, 'data') and response.data:
                columns = list(response.data[0].keys())
                rows = response.data

                # Форматируем данные
                formatted_rows = []
                for row in rows:
                    formatted_row = []
                    for col in columns:
                        value = row.get(col)
                        if value is None:
                            formatted_row.append("NULL")
                        elif isinstance(value, str) and len(value) > 30:
                            formatted_row.append(value[:27] + "...")
                        else:
                            formatted_row.append(str(value))
                    formatted_rows.append(formatted_row)

                print(f"\n📋 Данные из {table_name}:")
                print(tabulate(formatted_rows, headers=columns, tablefmt="grid"))
                print(f"\nПоказано записей: {len(rows)}")
            else:
                print("ℹ️ Таблица пуста")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def _select_columns(self, table_name: str, columns_str: str):
        """Выбрать определенные столбцы"""
        try:
            columns = [col.strip() for col in columns_str.split(',')]
            response = self.supabase.table(table_name).select(','.join(columns)).limit(10).execute()

            if hasattr(response, 'data') and response.data:
                rows = response.data

                # Форматируем данные
                formatted_rows = []
                for row in rows:
                    formatted_row = []
                    for col in columns:
                        value = row.get(col)
                        if value is None:
                            formatted_row.append("NULL")
                        elif isinstance(value, str) and len(value) > 30:
                            formatted_row.append(value[:27] + "...")
                        else:
                            formatted_row.append(str(value))
                    formatted_rows.append(formatted_row)

                print(f"\n📋 Данные из {table_name} (столбцы: {columns_str}):")
                print(tabulate(formatted_rows, headers=columns, tablefmt="grid"))
            else:
                print("ℹ️ Данные не найдены")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def _filter_table(self, table_name: str, column: str, value: str, operator: str = "="):
        """Фильтровать таблицу"""
        try:
            # Преобразуем оператор в формат Supabase
            supabase_operators = {
                '=': 'eq',
                '!=': 'neq',
                '>': 'gt',
                '<': 'lt',
                '>=': 'gte',
                '<=': 'lte',
                'like': 'like'
            }

            if operator in supabase_operators:
                supabase_op = supabase_operators[operator]
                query = self.supabase.table(table_name).select('*').filter(column, supabase_op, value).limit(
                    10).execute()
            else:
                print(f"❌ Неподдерживаемый оператор: {operator}")
                return

            if hasattr(query, 'data') and query.data:
                columns = list(query.data[0].keys())
                rows = query.data

                # Форматируем данные
                formatted_rows = []
                for row in rows:
                    formatted_row = []
                    for col in columns:
                        value = row.get(col)
                        if value is None:
                            formatted_row.append("NULL")
                        elif isinstance(value, str) and len(value) > 30:
                            formatted_row.append(value[:27] + "...")
                        else:
                            formatted_row.append(str(value))
                    formatted_rows.append(formatted_row)

                print(f"\n📋 Данные из {table_name} ({column} {operator} {value}):")
                print(tabulate(formatted_rows, headers=columns, tablefmt="grid"))
                print(f"\nНайдено записей: {len(rows)}")
            else:
                print("ℹ️ Данные по фильтру не найдены")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def _sort_table(self, table_name: str, column: str, order: str = "asc"):
        """Сортировать таблицу"""
        try:
            response = self.supabase.table(table_name).select('*').order(column, desc=(order.lower() == 'desc')).limit(
                10).execute()

            if hasattr(response, 'data') and response.data:
                columns = list(response.data[0].keys())
                rows = response.data

                # Форматируем данные
                formatted_rows = []
                for row in rows:
                    formatted_row = []
                    for col in columns:
                        value = row.get(col)
                        if value is None:
                            formatted_row.append("NULL")
                        elif isinstance(value, str) and len(value) > 30:
                            formatted_row.append(value[:27] + "...")
                        else:
                            formatted_row.append(str(value))
                    formatted_rows.append(formatted_row)

                print(f"\n📋 Данные из {table_name} (сортировка по {column} {order}):")
                print(tabulate(formatted_rows, headers=columns, tablefmt="grid"))
            else:
                print("ℹ️ Таблица пуста")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def explore_table_interactively(self):
        """Интерактивное исследование таблиц"""
        tables = self.discover_tables()

        if not tables:
            print("❌ Не обнаружено таблиц для исследования")
            return

        while True:
            print("\n" + "=" * 50)
            print("ИССЛЕДОВАНИЕ ТАБЛИЦ")
            print("=" * 50)

            print("\nДоступные таблицы:")
            for i, table in enumerate(tables, 1):
                count = self.get_table_row_count(table)
                print(f"  {i:2}. {table:<25} [~{count} записей]")

            print("\n 0. Выход")

            try:
                choice = input("\nВыберите таблицу (номер, или 0 для выхода): ").strip()

                if choice == "0":
                    break

                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(tables):
                    table_name = tables[choice_idx]
                    self.execute_custom_query(table_name)
                else:
                    print("❌ Неверный выбор")

            except ValueError:
                print("❌ Введите номер таблицы")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

    def run_full_analysis(self):
        """Запустить полный анализ базы данных"""
        self.print_header("ПОЛНЫЙ АНАЛИЗ БАЗЫ ДАННЫХ SUPABASE")

        # 1. Информация о проекте
        self.print_database_info()

        # 2. Все таблицы
        self.print_all_tables()

        # 3. Статистика
        self.print_table_statistics()

        # 4. Исследование
        tables = self.discover_tables()
        if tables:
            print("\n" + "=" * 80)
            explore = input("Хотите исследовать таблицы интерактивно? (y/n): ").lower()
            if explore == 'y':
                self.explore_table_interactively()


def main():
    """Основная функция"""
    print("🔍 ИНСПЕКТОР БАЗЫ ДАННЫХ SUPABASE")
    print("=" * 50)

    # Используем ваши данные по умолчанию
    default_url = "https://dsmbawejfgcxfchscfyt.supabase.co"
    default_key = "sb_publishable_x6bTuw7rUEn7mfXmV7MvmA_XPrNrATU"

    print(f"URL по умолчанию: {default_url}")
    print(f"Key по умолчанию: {default_key[:20]}...")

    use_default = input("\nИспользовать настройки по умолчанию? (y/n): ").lower().strip()

    if use_default == 'y':
        url = default_url
        key = default_key
    else:
        url = input(f"Supabase URL [{default_url}]: ").strip() or default_url
        key = input(f"Supabase Key [{default_key}]: ").strip() or default_key

    inspector = SupabaseInspector(url, key)

    if not inspector.connect():
        print("\nПроблемы с подключением. Проверьте:")
        print("1. Правильность URL и ключа")
        print("2. Доступность интернета")
        print("3. Настройки CORS в Supabase Dashboard")
        print("4. Роли и права доступа в Supabase")
        sys.exit(1)

    try:
        # Выбор режима работы
        print("\n" + "=" * 50)
        print("Режимы работы:")
        print("  1. Полный анализ базы данных")
        print("  2. Исследовать таблицы интерактивно")
        print("  3. Ручной ввод названия таблицы")
        print("  0. Выйти")

        mode = input("\nВыберите режим (0-3): ").strip()

        if mode == "0":
            print("👋 Выход")
        elif mode == "1":
            inspector.run_full_analysis()
        elif mode == "2":
            inspector.explore_table_interactively()
        elif mode == "3":
            table_name = input("Введите название таблицы: ").strip()
            if table_name:
                inspector.print_table_details(table_name)
        else:
            print("❌ Неверный режим. Запускаю полный анализ...")
            inspector.run_full_analysis()

        print("\n" + "=" * 50)
        print("✅ Анализ завершен!")

        # Предложение экспорта
        export = input("\nЭкспортировать информацию в файл? (y/n): ").lower()
        if export == 'y':
            filename = input("Имя файла [supabase_info.txt]: ").strip() or "supabase_info.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                import datetime
                f.write(f"Отчет анализа Supabase\n")
                f.write(f"Дата: {datetime.datetime.now()}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Key: {key[:20]}...\n\n")

                tables = inspector.discover_tables()
                f.write(f"Обнаружено таблиц: {len(tables)}\n")
                for table in tables:
                    count = inspector.get_table_row_count(table)
                    f.write(f"- {table}: ~{count} записей\n")

            print(f"✅ Информация экспортирована в {filename}")

    except KeyboardInterrupt:
        print("\n\n⚠️ Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()