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

# Создаем директорию для скриптов
RUN mkdir -p /app/scripts

# Делаем скрипты исполняемыми
RUN chmod +x /app/scripts/*.py 2>/dev/null || true

# Создаем директории для базы данных и медиафайлов
RUN mkdir -p /app/db /app/media /app/staticfiles

# Открываем порт для приложения
EXPOSE 8000

# Запускаем приложение
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
