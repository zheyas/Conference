import os
import uuid

from django.db import models
from django.core.exceptions import ValidationError
from datetime import date


def document_upload_path(instance, filename):
    """Генерирует путь для загружаемого документа"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('file', filename)


class ConferenceInfo(models.Model):
    """Основная информация о конференции"""

    title = models.CharField(
        max_length=200,
        default='IT-Весна 2026',
        verbose_name='Название конференции'
    )

    subtitle = models.CharField(
        max_length=300,
        default='Студенческая научно-техническая конференция',
        verbose_name='Подзаголовок'
    )

    description = models.TextField(
        max_length=1000,
        default='Ежегодная студенческая конференция для молодых исследователей...',
        verbose_name='Описание'
    )

    start_date = models.DateField(
        verbose_name='Дата начала',
        default=date(2026, 5, 15)
    )

    end_date = models.DateField(
        verbose_name='Дата окончания',
        default=date(2026, 5, 17)
    )

    location = models.CharField(
        max_length=200,
        default='Главный корпус ОГУ',
        verbose_name='Место проведения'
    )

    submission_deadline = models.DateField(
        verbose_name='Дедлайн подачи тезисов',
        default=date(2026, 4, 1)
    )

    notification_date = models.DateField(
        verbose_name='Дата уведомления о принятии',
        default=date(2026, 4, 15)
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Информация о конференции'
        verbose_name_plural = 'Информация о конференции'

    def __str__(self):
        return self.title

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError('Дата начала не может быть позже даты окончания')

    def get_dates_display(self):
        """Форматированный вывод дат"""
        if self.start_date == self.end_date:
            return self.start_date.strftime('%d.%m.%Y')
        return f"{self.start_date.strftime('%d.%m')} - {self.end_date.strftime('%d.%m.%Y')}"


class ImportantDate(models.Model):
    """Важные даты конференции"""

    title = models.CharField(
        max_length=200,
        verbose_name='Название события'
    )

    date = models.DateField(
        verbose_name='Дата'
    )

    description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Описание'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )

    class Meta:
        verbose_name = 'Важная дата'
        verbose_name_plural = 'Важные даты'
        ordering = ['order', 'date']

    def __str__(self):
        return f"{self.title} - {self.date.strftime('%d.%m.%Y')}"


class Contact(models.Model):
    """Контакты оргкомитета с поддержкой разных типов иконок"""

    CONTACT_TYPES = [
        ('email', 'Email'),
        ('phone', 'Телефон'),
        ('address', 'Адрес'),
        ('social', 'Социальная сеть'),
        ('other', 'Другое'),
    ]

    ICON_TYPES = [
        ('bootstrap', 'Bootstrap Icon'),
        ('image', 'Загруженное изображение'),
        ('url', 'Ссылка на изображение'),
    ]

    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPES,
        verbose_name='Тип контакта'
    )

    title = models.CharField(
        max_length=100,
        verbose_name='Название',
        help_text='Например: "Оргкомитет", "Техническая поддержка"'
    )

    value = models.CharField(
        max_length=200,
        verbose_name='Значение'
    )

    # Тип иконки
    icon_type = models.CharField(
        max_length=20,
        choices=ICON_TYPES,
        default='bootstrap',
        verbose_name='Тип иконки'
    )

    # Для Bootstrap иконок
    icon_bootstrap = models.CharField(
        max_length=50,
        blank=True,
        help_text='Класс иконки (например: bi-envelope, bi-telephone)',
        verbose_name='Bootstrap иконка'
    )

    # Для загруженных изображений
    icon_image = models.ImageField(
        upload_to='contacts/icons/',
        verbose_name='Иконка (изображение)',
        help_text='Загрузите изображение для иконки (рекомендуемый размер: 100x100px)',
        blank=True,
        null=True
    )

    # Для изображений по ссылке
    icon_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='Ссылка на иконку',
        help_text='URL изображения для иконки (например, с Gravatar или другого сервиса)'
    )

    # Запасная иконка на случай, если не загрузится по ссылке
    icon_fallback = models.ImageField(
        upload_to='contacts/fallback/',
        verbose_name='Запасная иконка',
        help_text='Изображение, которое покажется, если не загрузится иконка по ссылке',
        blank=True,
        null=True
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        ordering = ['order', 'contact_type']

    def __str__(self):
        return f"{self.get_contact_type_display()}: {self.title}"

    def get_icon_data(self):
        """Возвращает данные для отображения иконки"""
        if self.icon_type == 'bootstrap' and self.icon_bootstrap:
            return {
                'type': 'bootstrap',
                'class': self.icon_bootstrap
            }
        elif self.icon_type == 'image' and self.icon_image:
            return {
                'type': 'image',
                'url': self.icon_image.url
            }
        elif self.icon_type == 'url' and self.icon_url:
            return {
                'type': 'url',
                'url': self.icon_url,
                'fallback': self.icon_fallback.url if self.icon_fallback else None
            }
        # Bootstrap по умолчанию на основе типа контакта
        default_icons = {
            'email': 'bi-envelope',
            'phone': 'bi-telephone',
            'address': 'bi-geo-alt',
            'social': 'bi-share',
            'other': 'bi-info-circle',
        }
        return {
            'type': 'bootstrap',
            'class': default_icons.get(self.contact_type, 'bi-info-circle')
        }


class Organizer(models.Model):
    """Организаторы конференции с поддержкой разных типов иконок"""

    ICON_TYPES = [
        ('bootstrap', 'Bootstrap Icon'),
        ('image', 'Загруженное изображение'),
        ('url', 'Ссылка на изображение'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )

    description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Описание'
    )

    website = models.URLField(
        blank=True,
        verbose_name='Сайт'
    )

    # Тип иконки
    icon_type = models.CharField(
        max_length=20,
        choices=ICON_TYPES,
        default='bootstrap',
        verbose_name='Тип иконки'
    )

    # Для Bootstrap иконок
    icon_bootstrap = models.CharField(
        max_length=50,
        blank=True,
        help_text='Класс иконки (например: bi-building, bi-people)',
        verbose_name='Bootstrap иконка'
    )

    # Для загруженных изображений
    icon_image = models.ImageField(
        upload_to='organizers/icons/',
        verbose_name='Иконка (изображение)',
        help_text='Загрузите изображение для иконки (рекомендуемый размер: 200x200px)',
        blank=True,
        null=True
    )

    # Для изображений по ссылке
    icon_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='Ссылка на иконку',
        help_text='URL изображения для иконки (например, логотип организации)'
    )

    # Запасная иконка на случай, если не загрузится по ссылке
    icon_fallback = models.ImageField(
        upload_to='organizers/fallback/',
        verbose_name='Запасная иконка',
        help_text='Изображение, которое покажется, если не загрузится иконка по ссылке',
        blank=True,
        null=True
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )

    class Meta:
        verbose_name = 'Организатор'
        verbose_name_plural = 'Организаторы'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_icon_data(self):
        """Возвращает данные для отображения иконки организатора"""
        if self.icon_type == 'bootstrap' and self.icon_bootstrap:
            return {
                'type': 'bootstrap',
                'class': self.icon_bootstrap
            }
        elif self.icon_type == 'image' and self.icon_image:
            return {
                'type': 'image',
                'url': self.icon_image.url
            }
        elif self.icon_type == 'url' and self.icon_url:
            return {
                'type': 'url',
                'url': self.icon_url,
                'fallback': self.icon_fallback.url if self.icon_fallback else None
            }
        # Bootstrap по умолчанию
        return {
            'type': 'bootstrap',
            'class': 'bi-building'
        }

class UsefulLink(models.Model):
    """Полезные ссылки в футере"""

    title = models.CharField(
        max_length=100,
        verbose_name='Название'
    )

    url = models.URLField(
        verbose_name='Ссылка'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )

    class Meta:
        verbose_name = 'Полезная ссылка'
        verbose_name_plural = 'Полезные ссылки'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title
