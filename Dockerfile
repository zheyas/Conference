# Используем официальный python-образ как базовый
FROM python:3.11-slim

# Устанавливаем зависимости для сборки Python пакетов и cron
RUN apt-get update && apt-get install -y \
    build-essential \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копируем requirements.txt отдельно для кэширования слоёв
COPY requirements.txt .

# Устанавливаем зависимости python
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем остальной проект в контейнер
COPY . .

# Создаем директорию для скриптов и базы данных
RUN mkdir -p /app/scripts /app/db /app/media /app/staticfiles /app/db_backups

# Делаем скрипты исполняемыми
RUN chmod +x /app/scripts/*.py /app/entrypoint.sh 2>/dev/null || true

# Создаем entrypoint скрипт для автоматического запуска миграций и создания суперпользователя
RUN echo '#!/bin/sh\n\
set -e\n\
echo "========================================="\n\
echo " ЗАПУСК КОНТЕЙНЕРА"\n\
echo "========================================="\n\
echo " Проверка базы данных..."\n\
if [ ! -f /app/db/db.sqlite3 ]; then\n\
  echo "   База данных не найдена, будет создана при миграциях"\n\
fi\n\
echo " Применение миграций..."\n\
python manage.py migrate\n\
echo " Создание суперпользователя..."\n\
python scripts/create_superuser_from_env.py\n\
echo " Настройка автоматических бэкапов..."\n\
echo "0 0 * * * cd /app && python scripts/backup_db.py backup >> /app/db_backups/cron.log 2>&1" | crontab -\n\
service cron start\n\
echo " Запуск сервера..."\n\
echo "========================================="\n\
exec python manage.py runserver 0.0.0.0:8000' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Открываем порт для приложения
EXPOSE 8000

# Запускаем entrypoint скрипт
ENTRYPOINT ["/app/entrypoint.sh"]