from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Создает администратора системы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email администратора'
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Пароль администратора'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Админ',
            help='Имя администратора'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='Системы',
            help='Фамилия администратора'
        )

    def handle(self, *args, **options):
        User = get_user_model()

        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Проверяем, существует ли уже пользователь
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Пользователь с email {email} уже существует'))
            return

        # Создаем администратора
        admin = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=True,
        )

        # Устанавливаем пароль
        admin.set_password(password)
        admin.save()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Администратор создан:\n'
            f'   Email: {email}\n'
            f'   Пароль: {password}\n'
            f'   Имя: {first_name} {last_name}\n'
            f'   Роль: Супер-администратор'
        ))
