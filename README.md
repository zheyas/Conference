# IT-Весна 2026 - Конференция ОГУ

Платформа для управления студенческой научно-технической конференцией "IT-Весна" Оренбургского государственного университета.

## Возможности

- Управление пользователями: регистрация, аутентификация, восстановление пароля с подтверждением по email
- Подача докладов: участники могут подавать доклады с файлами (текст, презентация, архив с материалами)
- Секции конференции: управление секциями, назначение председателей жюри
- Модерация: административная панель для обработки докладов, изменение статусов с автоматической отправкой уведомлений
- Уведомления: email-уведомления при изменении статуса доклада (принят, отклонен, требует доработки)
- Документооборот: загрузка и скачивание документов конференции (положения, программы)
- Статистика: отслеживание количества докладов, авторов, сертификатов
- Резервное копирование: автоматическое создание бэкапов базы данных

## Технологии

- Backend: Python 3.11, Django 5.2
- Frontend: HTML, CSS, Tailwind CSS, Bootstrap Icons
- База данных: SQLite
- Контейнеризация: Docker, Docker Compose
- Email: SMTP (Mail.ru / Yandex)
- Деплой: Render.com

## Требования

- Docker и Docker Compose (рекомендуемый способ)
- Git
- Python 3.10+ (только для локальной разработки без Docker)

## Быстрый старт с Docker

### 1. Клонировать репозиторий

```bash
git clone https://github.com/zheyas/Conference.git
cd Conference
```

### 2. Настроить переменные окружения

Создайте файл `.env` в корне проекта по примеру `.env.example`:


### 3. Запустить через Docker Compose

```bash
# Сборка и запуск в фоновом режиме
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

### 4. Доступ к приложению

- Сайт: http://localhost:8000
- Админ-панель: http://localhost:8000/admin
- Данные для входа: используйте `SUPERUSER_EMAIL` и `SUPERUSER_PASSWORD` из `.env`

## Запуск без Docker (локальная разработка)

### 1. Создать виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить переменные окружения

Создайте файл `.env` (аналогично Docker, но без Docker-путей)

### 4. Применить миграции и запустить

```bash
python manage.py migrate
python manage.py runserver или docker-compose up
```

## Работа с Docker

### Основные команды

```bash
# Запуск контейнеров
docker-compose up -d

# Остановка контейнеров
docker-compose down

# Перезапуск с пересборкой
docker-compose down
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f nginx

# Выполнение команд внутри контейнера
docker-compose exec backend python manage.py shell
docker-compose exec backend python manage.py createsuperuser
```

### Работа с базой данных

```bash
# Создать резервную копию вручную
docker-compose exec backend python scripts/backup_db.py backup

# Посмотреть список бэкапов
docker-compose exec backend python scripts/backup_db.py list

# Восстановить из бэкапа (например, номер 1)
docker-compose exec backend python scripts/backup_db.py restore 1

# Подключиться к базе данных SQLite
docker-compose exec backend sqlite3 /app/db/db.sqlite3
.tables
```

### Работа с файлами

```bash
# Просмотр загруженных файлов
docker-compose exec backend ls -la /app/media/

# Просмотр статических файлов
docker-compose exec backend ls -la /app/staticfiles/

# Просмотр бэкапов
docker-compose exec backend ls -la /app/db_backups/
```

## Структура томов Docker

Проект использует именованные тома для сохранения данных:

- `sqlite_data` - база данных (не должна теряется при перезапуске)
- `media_data` - загруженные пользователями файлы
- `static_data` - статические файлы
- `backup_data` - резервные копии базы данных

## Переменные окружения

| Переменная | Описание | Пример                    |
|------------|----------|---------------------------|
| `DEBUG` | Режим отладки | `True` / `False`          |
| `SECRET_KEY` | Секретный ключ Django | `django-insecure-...`     |
| `DJANGO_ALLOWED_HOSTS` | Разрешенные хосты | `localhost,127.0.0.1,...` |
| `CSRF_TRUSTED_ORIGINS` | Доверенные источники для CSRF | `http://localhost:8000`   |
| `SUPERUSER_EMAIL` | Email суперпользователя | `admin@example.com`       |
| `SUPERUSER_PASSWORD` | Пароль суперпользователя | `password123`             |
| `SUPERUSER_FIRST_NAME` | Имя суперпользователя | `Admin`                   |
| `SUPERUSER_LAST_NAME` | Фамилия суперпользователя | `Super`                   |
| `EMAIL_HOST_USER` | Email для отправки уведомлений | `it-spring.osu@mail.ru`   |
| `EMAIL_HOST_PASSWORD` | Пароль приложения для email | `app-password`            |
| `DEFAULT_FROM_EMAIL` | Email отправителя | `it-spring.osu@mail.ru`   |



## Полезные ссылки

- Репозиторий: https://github.com/zheyas/Conference
- Документация Django: https://docs.djangoproject.com/
- Документация Docker: https://docs.docker.com/
- Render: https://render.com

## Тестовый стенд

https://conference-rnik.onrender.com

