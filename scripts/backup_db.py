#!/usr/bin/env python
import os
import sys
import shutil
import datetime
from pathlib import Path

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent / 'db' / 'db.sqlite3'
BACKUP_DIR = Path(__file__).parent.parent / 'db_backups'


def create_backup():
    """Создает резервную копию базы данных"""

    # Проверяем, существует ли база данных
    if not DB_PATH.exists():
        print(f"[!] База данных не найдена по пути: {DB_PATH}")
        return False

    # Создаем папку для бэкапов если её нет
    BACKUP_DIR.mkdir(exist_ok=True)

    # Формируем имя файла с датой
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'db_backup_{timestamp}.sqlite3'

    # Копируем файл
    try:
        shutil.copy2(DB_PATH, backup_file)
        print(f"[+] Резервная копия создана: {backup_file}")
        print(f"    Размер: {backup_file.stat().st_size / 1024 / 1024:.2f} MB")

        # Оставляем только последние 3 бэкапа
        backups = sorted(BACKUP_DIR.glob('db_backup_*.sqlite3'))
        if len(backups) > 3:
            for old_backup in backups[:-3]:
                old_backup.unlink()
                print(f"    [-] Удален старый бэкап: {old_backup.name}")

        return True
    except Exception as e:
        print(f"[!] Ошибка при создании бэкапа: {e}")
        return False


def restore_backup(backup_file):
    """Восстанавливает базу данных из резервной копии"""

    backup_path = Path(backup_file)

    if not backup_path.exists():
        print(f"[!] Файл бэкапа не найден: {backup_path}")
        return False

    try:
        # Создаем бэкап текущей базы перед восстановлением
        if DB_PATH.exists():
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore_backup = BACKUP_DIR / f'pre_restore_{timestamp}.sqlite3'
            shutil.copy2(DB_PATH, pre_restore_backup)
            print(f"[+] Создан бэкап текущей БД: {pre_restore_backup}")

        # Восстанавливаем
        shutil.copy2(backup_path, DB_PATH)
        print(f"[+] База данных восстановлена из: {backup_path}")
        return True
    except Exception as e:
        print(f"[!] Ошибка при восстановлении: {e}")
        return False


def list_backups():
    """Показывает список доступных бэкапов"""

    if not BACKUP_DIR.exists():
        print("[!] Папка с бэкапами не найдена")
        return

    backups = sorted(BACKUP_DIR.glob('db_backup_*.sqlite3'), reverse=True)

    if not backups:
        print("[-] Нет доступных бэкапов")
        return

    print("\n[+] Доступные резервные копии:")
    print("-" * 60)
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / 1024 / 1024
        mod_time = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{i}. {backup.name}")
        print(f"   Размер: {size:.2f} MB, Дата: {mod_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print("-" * 60)


if __name__ == '__main__':
    print("=" * 60)
    print("[ УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ ]")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("Использование:")
        print("  python scripts/backup_db.py backup     - создать бэкап")
        print("  python scripts/backup_db.py list       - показать бэкапы")
        print("  python scripts/backup_db.py restore N  - восстановить из бэкапа N")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'backup':
        create_backup()
    elif command == 'list':
        list_backups()
    elif command == 'restore' and len(sys.argv) == 3:
        try:
            num = int(sys.argv[2])
            backups = sorted(BACKUP_DIR.glob('db_backup_*.sqlite3'), reverse=True)
            if 1 <= num <= len(backups):
                restore_backup(backups[num - 1])
            else:
                print(f"[!] Неверный номер бэкапа. Доступны: 1-{len(backups)}")
        except ValueError:
            print("[!] Укажите номер бэкапа")
    else:
        print("[!] Неизвестная команда")
