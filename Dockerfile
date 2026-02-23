# Используем официальный python-образ как базовый
FROM python:3.11-slim

# Устанавливаем зависимости для сборки Python пакетов
RUN apt-get update && apt-get install -y \
    build-essential \
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
RUN mkdir -p /app/scripts /app/db /app/media /app/staticfiles

# Делаем скрипты исполняемыми
RUN chmod +x /app/scripts/*.py 2>/dev/null || true

# Создаем entrypoint скрипт для автоматического запуска миграций и создания суперпользователя
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Running database migrations..."\n\
python manage.py migrate\n\
echo "Creating superuser if not exists..."\n\
python /app/scripts/create_superuser.py\n\
echo "Starting server..."\n\
exec python manage.py runserver 0.0.0.0:8000' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Открываем порт для приложения
EXPOSE 8000

# Запускаем entrypoint скрипт
ENTRYPOINT ["/app/entrypoint.sh"]