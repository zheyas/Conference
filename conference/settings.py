import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-58v15$*qkfxb7p=_egss!oio$fto@*=&j*d_@)dmp+l+^&^a0q')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://conference-rnik.onrender.com',
    'http://conference-rnik.onrender.com',
]

if os.getenv('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS.extend(os.getenv('CSRF_TRUSTED_ORIGINS').split(','))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'docs',
    'core',
    'users',
    'talks',
    'authors',
    'conference_admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'conference.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.core_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'conference.wsgi.application'

# Database - определяем путь в зависимости от окружения
# Проверяем, запущены ли мы в Docker
IN_DOCKER = os.path.exists('/.dockerenv') or os.path.exists('/app/.dockerenv')

if IN_DOCKER or os.getenv('DB_PATH'):  # В Docker или явно указан путь
    DB_PATH = Path(os.getenv('DB_PATH', '/app/db/db.sqlite3'))
else:  # Локально
    DB_PATH = BASE_DIR / 'db' / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(DB_PATH),
    }
}

# Создаем директорию для базы данных, если её нет
# Но только если мы НЕ в Docker (в Docker volume уже создан)
if not IN_DOCKER:
    try:
        db_parent = DB_PATH.parent
        db_parent.mkdir(parents=True, exist_ok=True)
        print(f"📁 Создана папка для БД: {db_parent}")
    except Exception as e:
        print(f"⚠️ Не удалось создать папку для БД: {e}")

# Проверяем доступность базы данных при запуске
try:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"✅ Путь к БД: {DB_PATH}")
    print(f"✅ Папка для БД: {DB_PATH.parent}")
    if DB_PATH.exists():
        print(f"✅ Файл БД существует, размер: {DB_PATH.stat().st_size / 1024:.1f} KB")
    else:
        print(f"ℹ️ Файл БД будет создан при первой миграции")
except Exception as e:
    print(f"⚠️ Ошибка при проверке БД: {e}")

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
if IN_DOCKER or os.getenv('STATIC_PATH'):
    STATIC_ROOT = os.getenv('STATIC_PATH', '/app/staticfiles')
else:
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
if IN_DOCKER or os.getenv('MEDIA_PATH'):
    MEDIA_ROOT = os.getenv('MEDIA_PATH', '/app/media')
else:
    MEDIA_ROOT = BASE_DIR / 'media'

# Создаем директории для медиа и статики локально
if not IN_DOCKER:
    Path(STATIC_ROOT).mkdir(parents=True, exist_ok=True)
    Path(MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'index'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
SERVER_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

SITE_NAME = "IT-Весна 2026"
SITE_URL = 'https://conference-rnik.onrender.com'

SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755