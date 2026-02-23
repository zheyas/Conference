#!/usr/bin/env python
import os
import re
import sys


def remove_emojis(text):
    """Удаляет эмодзи из текста"""
    # Паттерн для поиска эмодзи
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # variation selectors
                               u"\u3030"
                               "]+", flags=re.UNICODE)

    return emoji_pattern.sub(r'', text)


def main():
    """Удаляет эмодзи из всех HTML файлов, кроме base.html и index.html"""

    templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'QuasWexExort/templates')

    # Исключаемые файлы
    exclude_files = [
        os.path.join(templates_dir, 'base.html'),
        os.path.join(templates_dir, 'index.html')
    ]

    total_files = 0
    modified_files = 0

    print("=" * 60)
    print("🔍 ПОИСК И УДАЛЕНИЕ ЭМОДЗИ В HTML ФАЙЛАХ")
    print("=" * 60)
    print(f"📁 Папка: {templates_dir}")
    print(f"🚫 Исключены: base.html, index.html")
    print()

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, templates_dir)

                # Пропускаем исключенные файлы
                if file_path in exclude_files:
                    print(f"⏩ Пропущен (исключение): {rel_path}")
                    continue

                total_files += 1

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Проверяем наличие эмодзи
                    new_content = remove_emojis(content)

                    if content != new_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)

                        modified_files += 1
                        print(f"✅ Удалены эмодзи: {rel_path}")
                    else:
                        print(f"⏩ Нет эмодзи: {rel_path}")

                except Exception as e:
                    print(f"❌ Ошибка при обработке {rel_path}: {e}")

    print("\n" + "=" * 60)
    print("📊 ИТОГ:")
    print(f"   Всего файлов: {total_files}")
    print(f"   Изменено файлов: {modified_files}")
    print("=" * 60)


if __name__ == '__main__':
    main()