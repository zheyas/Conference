#authors/models.py
from django.db import models
import uuid
from django.conf import settings


class Author(models.Model):
    """Автор доклада (отдельная сущность)"""

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['last_name', 'first_name']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Основные поля автора
    first_name = models.CharField(
        max_length=100,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name='Фамилия'
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отчество'
    )

    email = models.EmailField(
        verbose_name='Электронная почта'
    )

    # Опциональная связь с пользователем системы (1 к 1, необязательная)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='author_profile',
        verbose_name='Пользователь системы'
    )

    # Дополнительная информация
    organization = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Организация'
    )

    department = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Кафедра/факультет'
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

    position = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Должность'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )

    orcid = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='ORCID ID'
    )

    scopus_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Scopus Author ID'
    )

    researcher_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='ResearcherID'
    )

    # Статус
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """Полное ФИО автора"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    def get_short_name(self):
        """Короткое имя (Фамилия И.О.)"""
        result = self.last_name
        if self.first_name:
            result += f' {self.first_name[0]}.'
        if self.middle_name:
            result += f'{self.middle_name[0]}.'
        return result

    def get_academic_info(self):
        """Академическая информация"""
        info = []
        if self.academic_degree:
            info.append(self.academic_degree)
        if self.academic_title:
            info.append(self.academic_title)
        return ', '.join(info)

    def get_affiliation(self):
        """Аффилиация автора"""
        parts = []
        if self.organization:
            parts.append(self.organization)
        if self.department:
            parts.append(self.department)
        return ', '.join(parts)


class AuthorRole(models.Model):
    """Роль автора в докладе"""

    class Meta:
        verbose_name = 'Роль автора'
        verbose_name_plural = 'Роли авторов'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=100,
        verbose_name='Название роли'
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код роли'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание роли'
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name='Основная роль'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )

    def __str__(self):
        return self.name


class AuthorReport(models.Model):
    """Связь автор-доклад с указанием роли"""

    class Meta:
        verbose_name = 'Автор доклада'
        verbose_name_plural = 'Авторы докладов'
        unique_together = ['author', 'report']
        ordering = ['order']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='report_authorships',
        verbose_name='Автор'
    )

    report = models.ForeignKey(
        'talks.Report',  # Ссылка на модель в приложении talks
        on_delete=models.CASCADE,
        related_name='author_reports',
        verbose_name='Доклад'
    )

    role = models.ForeignKey(
        AuthorRole,
        on_delete=models.SET_NULL,
        null=True,
        related_name='author_reports',
        verbose_name='Роль'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок в списке авторов'
    )

    # Флаг основного автора (для обратной совместимости)
    is_main_author = models.BooleanField(
        default=False,
        verbose_name='Основной автор'
    )

    # Дополнительные поля
    contribution = models.TextField(
        blank=True,
        verbose_name='Вклад в работу'
    )

    corresponding_author = models.BooleanField(
        default=False,
        verbose_name='Автор для корреспонденции'
    )

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author} - {self.report} ({self.role.name if self.role else 'Без роли'})"

    def save(self, *args, **kwargs):
        # Если роль является основной, устанавливаем флаг is_main_author
        if self.role and self.role.is_main:
            self.is_main_author = True
        super().save(*args, **kwargs)
