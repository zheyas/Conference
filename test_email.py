import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conference.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("=" * 60)
print("🔧 ТЕСТОВАЯ ОТПРАВКА ПИСЬМА (Mail.ru)")
print("=" * 60)
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email User: {settings.EMAIL_HOST_USER}")
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"Using SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
print(f"Password loaded: {'Да' if settings.EMAIL_HOST_PASSWORD else 'Нет'}")
print("=" * 60)

try:
    send_mail(
        '✅ IT-Весна: Тест через Mail.ru',
        f'''Здравствуйте!

Это тестовое письмо отправлено через почтовый сервер Mail.ru.
Настройки:
- Сервер: {settings.EMAIL_HOST}
- Порт: {settings.EMAIL_PORT}
- SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}

Время отправки: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

С уважением,
Оргкомитет IT-Весна''',
        settings.DEFAULT_FROM_EMAIL,
        ['zhenyayasakov@yandex.ru'],
        fail_silently=False,
    )
    print("✅ Письмо успешно отправлено!")
except Exception as e:
    print(f"❌ Ошибка: {e}")