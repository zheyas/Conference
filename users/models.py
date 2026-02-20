#users/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid


class UserManager(BaseUserManager):
    """Менеджер для модели User с email вместо username"""

    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Модель пользователя"""

    class Role(models.TextChoices):
        USER = 'user', 'Участник'
        REVIEWER = 'reviewer', 'Рецензент'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор конференции'
        SUPER_ADMIN = 'super_admin', 'Супер-администратор'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Основные поля автора
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Фамилия'
    )

    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Имя'
    )

    middle_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Отчество'
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )

    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта'
    )

    # Роль пользователя в системе
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Роль'
    )

    # Дополнительные поля
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )

    organization = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Организация'
    )

    position = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Должность'
    )

    academic_degree = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ученая степень'
    )

    academic_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ученое звание'
    )

    # Переопределяем username для использования email
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Полное имя с отчеством"""
        parts = []
        if self.last_name:
            parts.append(self.last_name)
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts) if parts else self.email

    def get_short_name(self):
        """Короткое имя (Фамилия И.О.)"""
        if self.last_name and self.first_name:
            result = self.last_name
            if self.first_name:
                result += f' {self.first_name[0]}.'
            if self.middle_name:
                result += f'{self.middle_name[0]}.'
            return result
        return self.email

    @property
    def is_conference_admin(self):
        """Проверяет, является ли пользователь администратором конференции"""
        return self.role in [self.Role.ADMIN, self.Role.SUPER_ADMIN, self.Role.MODERATOR] or self.is_superuser

    @property
    def is_reviewer(self):
        """Проверяет, является ли пользователь рецензентом"""
        return self.role == self.Role.REVIEWER

    @property
    def can_review_reports(self):
        """Может ли пользователь рецензировать доклады"""
        return self.is_conference_admin or self.is_reviewer

    @property
    def is_jury_chairman(self):
        """Проверяет, является ли пользователь председателем жюри"""
        return self.chairman_sections.exists()

    @property
    def is_jury_member(self):
        """Проверяет, является ли пользователь членом жюри"""
        return self.jury_sections.exists()

