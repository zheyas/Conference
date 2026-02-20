import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver


def default_date():
    return timezone.now().date()


def default_time():
    return timezone.now().time()


def report_file_path(instance, filename):
    """Генерирует путь для файла доклада"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('reports', str(instance.id)[:2], filename)


def section_icon_path(instance, filename):
    """Генерирует путь для иконки секции"""
    ext = filename.split('.')[-1]
    filename = f"section_{uuid.uuid4()}.{ext}"
    return os.path.join('sections/icons', filename)


def certificate_file_path(instance, filename):
    """Генерирует путь для файла грамоты/сертификата"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('certificates', str(instance.report.id)[:2], filename)


class Section(models.Model):
    """Секция/тематика доклада"""

    class Meta:
        verbose_name = 'Секция'
        verbose_name_plural = 'Секции'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=200,
        verbose_name='Название секции'
    )

    description = models.TextField(
        verbose_name='Описание секции'
    )

    icon = models.ImageField(
        upload_to=section_icon_path,
        verbose_name='Иконка/логотип секции',
        help_text='Изображение для секции (рекомендуемый размер: 200x200px)',
        blank=True,
        null=True
    )

    date = models.DateField(
        verbose_name='Дата проведения',
        help_text='Дата проведения секции',
        default=timezone.now
    )

    time = models.TimeField(
        verbose_name='Время начала',
        help_text='Время начала секции',
        default=timezone.now
    )

    location = models.CharField(
        max_length=200,
        verbose_name='Место проведения',
        help_text='Аудитория или зал',
        default=''
    )

    jury_chairman = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chairman_sections',
        verbose_name='Председатель жюри'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_full_date(self):
        """Полная дата и время проведения"""
        return f"{self.date} в {self.time}"


class Report(models.Model):
    """Доклад/презентация"""

    class Meta:
        verbose_name = 'Доклад'
        verbose_name_plural = 'Доклады'
        ordering = ['-created_at']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Основные поля
    title = models.CharField(
        max_length=500,
        verbose_name='Название доклада'
    )

    abstract = models.TextField(
        verbose_name='Аннотация доклада',
        help_text='Краткое описание доклада (200-500 слов)',
        blank=True,
        null=True,
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name='Секция'
    )

    # Файлы
    report_file = models.FileField(
        upload_to=report_file_path,
        verbose_name='Доклад (Word/PDF)',
        help_text='Текст доклада в формате DOC, DOCX или PDF'
    )

    presentation_file = models.FileField(
        upload_to=report_file_path,
        verbose_name='Презентация',
        help_text='Презентация в формате PPT, PPTX или PDF',
        blank=True,
        null=True
    )

    media_archive = models.FileField(
        upload_to=report_file_path,
        verbose_name='Архив с фото/видео',
        help_text='ZIP или RAR архив с фотографиями и видео (макс. 50MB)',
        blank=True,
        null=True
    )

    # Пользователь, создавший доклад
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports',
        verbose_name='Создатель'
    )

    # Статус
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('submitted', 'Подано'),
        ('review', 'На рассмотрении'),
        ('approved', 'Допущено до очного тура'),
        ('rejected', 'Отклонено'),
        ('revisions_required', 'Требуются доработки'),
        ('resubmitted', 'Подано повторно'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус'
    )

    # Дополнительные поля
    keywords = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Ключевые слова',
        help_text='Ключевые слова через запятую'
    )

    doi = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='DOI'
    )

    # Комментарии администратора
    admin_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий администратора',
        help_text='Замечания и предложения для авторов'
    )

    # Описание внесенных изменений при повторной отправке
    revision_description = models.TextField(
        blank=True,
        verbose_name='Описание внесенных изменений',
        help_text='Что было исправлено в докладе после замечаний'
    )

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resubmitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_file_extension(self, file_type='report'):
        """Получить расширение файла"""
        file_map = {
            'report': self.report_file,
            'presentation': self.presentation_file,
            'media': self.media_archive
        }
        file_field = file_map.get(file_type)
        if file_field:
            return os.path.splitext(file_field.name)[1][1:].upper()
        return ''

    def get_file_size(self, file_type='report'):
        """Получить размер файла в читаемом формате"""
        file_map = {
            'report': self.report_file,
            'presentation': self.presentation_file,
            'media': self.media_archive
        }
        file_field = file_map.get(file_type)
        try:
            if file_field and hasattr(file_field, 'size'):
                size = file_field.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.1f} MB"
        except:
            pass
        return "N/A"

    def get_authors(self):
        """Получить всех авторов"""
        from authors.models import AuthorReport
        return AuthorReport.objects.filter(
            report=self,
            role__code='author'
        ).select_related('author').order_by('order')

    def get_supervisors(self):
        """Получить всех научных руководителей"""
        from authors.models import AuthorReport
        return AuthorReport.objects.filter(
            report=self,
            role__code='supervisor'
        ).select_related('author').order_by('order')

    def get_corresponding_authors(self):
        """Получить авторов для корреспонденции"""
        from authors.models import AuthorReport
        return AuthorReport.objects.filter(
            report=self,
            corresponding_author=True
        ).select_related('author').order_by('order')

    def get_all_participants(self):
        """Получить всех участников (авторов и руководителей)"""
        from authors.models import AuthorReport
        return AuthorReport.objects.filter(
            report=self
        ).select_related('author', 'role').order_by('order')

    def can_be_resubmitted(self):
        """Может ли доклад быть отправлен повторно (без проверки пользователя)"""
        return self.status == 'revisions_required'

    def can_be_resubmitted_by_author(self, user):
        """Может ли автор повторно отправить доклад после доработок"""
        is_author_or_creator = (
                self.created_by == user or
                self.author_reports.filter(author__user=user).exists()
        )

        if not is_author_or_creator:
            return False

        return self.status == 'revisions_required'

    @property
    def needs_resubmission(self):
        """Нуждается ли доклад в повторной отправке"""
        return self.status == 'revisions_required'

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем время подачи при смене статуса
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()

        # Автоматически устанавливаем время повторной отправки
        if self.status == 'resubmitted' and not self.resubmitted_at:
            self.resubmitted_at = timezone.now()

        # Автоматически устанавливаем время рассмотрения
        if self.status in ['approved', 'rejected', 'revisions_required'] and not self.reviewed_at:
            self.reviewed_at = timezone.now()

        super().save(*args, **kwargs)


class Certificate(models.Model):
    """Грамота/сертификат участника"""

    class Meta:
        verbose_name = 'Грамота/сертификат'
        verbose_name_plural = 'Грамоты/сертификаты'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Доклад'
    )

    author = models.ForeignKey(
        'authors.Author',
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Автор'
    )

    CERTIFICATE_TYPES = [
        ('participation', 'Сертификат участника'),
        ('winner', 'Грамота победителя'),
        ('diploma', 'Диплом'),
        ('thank_you', 'Благодарность'),
    ]

    certificate_type = models.CharField(
        max_length=20,
        choices=CERTIFICATE_TYPES,
        default='participation',
        verbose_name='Тип документа'
    )

    place = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Место (если призовое)'
    )

    nomination = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Номинация'
    )

    file = models.FileField(
        upload_to=certificate_file_path,
        verbose_name='Файл документа'
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_certificates',
        verbose_name='Кем выдан'
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата выдачи'
    )

    is_published = models.BooleanField(
        default=False,
        verbose_name='Опубликован'
    )

    def __str__(self):
        return f"{self.get_certificate_type_display()} для {self.author.get_full_name()}"


class JuryMember(models.Model):
    """Член жюри секции (может быть пользователем или произвольным человеком)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='jury_members_list',
        verbose_name='Секция'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jury_memberships',
        null=True,
        blank=True,
        verbose_name='Пользователь системы'
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        blank=True
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        blank=True
    )

    middle_name = models.CharField(
        max_length=150,
        verbose_name='Отчество',
        blank=True
    )

    organization = models.CharField(
        max_length=300,
        verbose_name='Организация',
        blank=True
    )

    position = models.CharField(
        max_length=200,
        verbose_name='Должность',
        blank=True
    )

    academic_degree = models.CharField(
        max_length=100,
        verbose_name='Ученая степень',
        blank=True
    )

    academic_title = models.CharField(
        max_length=100,
        verbose_name='Ученое звание',
        blank=True
    )

    email = models.EmailField(
        verbose_name='Электронная почта',
        blank=True
    )

    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон',
        blank=True
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Член жюри'
        verbose_name_plural = 'Члены жюри'
        ordering = ['order', 'last_name', 'first_name']
        unique_together = ['section', 'user']

    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name()} (пользователь)"
        else:
            return self.get_full_name()

    def get_full_name(self):
        """Полное имя члена жюри"""
        if self.user:
            return self.user.get_full_name()
        else:
            parts = []
            if self.last_name:
                parts.append(self.last_name)
            if self.first_name:
                parts.append(self.first_name)
            if self.middle_name:
                parts.append(self.middle_name)
            return ' '.join(parts) if parts else "Неизвестный член жюри"

    def get_short_name(self):
        """Короткое имя"""
        if self.user:
            return self.user.get_short_name()
        else:
            if self.last_name and self.first_name:
                result = self.last_name
                if self.first_name:
                    result += f' {self.first_name[0]}.'
                if self.middle_name:
                    result += f'{self.middle_name[0]}.'
                return result
            return "Член жюри"


# ========== СИГНАЛЫ ДЛЯ УДАЛЕНИЯ ФАЙЛОВ ==========
# ВСЕ СИГНАЛЫ ДОЛЖНЫ БЫТЬ ПОСЛЕ ОПРЕДЕЛЕНИЯ ВСЕХ КЛАССОВ!

@receiver(models.signals.post_delete, sender=Section)
def auto_delete_section_icon_on_delete(sender, instance, **kwargs):
    """Удаляет иконку секции при удалении записи"""
    import os
    if instance.icon and os.path.isfile(instance.icon.path):
        os.remove(instance.icon.path)
        print(f" Удалена иконка секции: {instance.icon.path}")


@receiver(models.signals.pre_save, sender=Section)
def auto_delete_section_icon_on_change(sender, instance, **kwargs):
    """Удаляет старую иконку при обновлении секции"""
    import os
    if not instance.pk:
        return False
    try:
        old_instance = Section.objects.get(pk=instance.pk)
    except Section.DoesNotExist:
        return False
    if old_instance.icon and old_instance.icon != instance.icon:
        if os.path.isfile(old_instance.icon.path):
            os.remove(old_instance.icon.path)
            print(f" Удалена старая иконка секции: {old_instance.icon.path}")


@receiver(models.signals.post_delete, sender=Report)
def auto_delete_report_files_on_delete(sender, instance, **kwargs):
    """Удаляет все файлы доклада при удалении записи"""
    import os
    if instance.report_file and os.path.isfile(instance.report_file.path):
        os.remove(instance.report_file.path)
        print(f" Удален файл доклада: {instance.report_file.path}")
    if instance.presentation_file and os.path.isfile(instance.presentation_file.path):
        os.remove(instance.presentation_file.path)
        print(f" Удалена презентация: {instance.presentation_file.path}")
    if instance.media_archive and os.path.isfile(instance.media_archive.path):
        os.remove(instance.media_archive.path)
        print(f" Удален архив с медиа: {instance.media_archive.path}")


@receiver(models.signals.pre_save, sender=Report)
def auto_delete_report_files_on_change(sender, instance, **kwargs):
    """Удаляет старые файлы при обновлении (замене)"""
    import os
    if not instance.pk:
        return False
    try:
        old_instance = Report.objects.get(pk=instance.pk)
    except Report.DoesNotExist:
        return False
    if old_instance.report_file and old_instance.report_file != instance.report_file:
        if os.path.isfile(old_instance.report_file.path):
            os.remove(old_instance.report_file.path)
            print(f" Удален старый файл доклада: {old_instance.report_file.path}")
    if old_instance.presentation_file and old_instance.presentation_file != instance.presentation_file:
        if os.path.isfile(old_instance.presentation_file.path):
            os.remove(old_instance.presentation_file.path)
            print(f" Удалена старая презентация: {old_instance.presentation_file.path}")
    if old_instance.media_archive and old_instance.media_archive != instance.media_archive:
        if os.path.isfile(old_instance.media_archive.path):
            os.remove(old_instance.media_archive.path)
            print(f" Удален старый архив с медиа: {old_instance.media_archive.path}")


@receiver(models.signals.post_delete, sender=Certificate)
def auto_delete_certificate_file_on_delete(sender, instance, **kwargs):
    """Удаляет файл сертификата при удалении записи"""
    import os
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)
        print(f" Удален файл сертификата: {instance.file.path}")


@receiver(models.signals.pre_save, sender=Certificate)
def auto_delete_certificate_file_on_change(sender, instance, **kwargs):
    """Удаляет старый файл сертификата при обновлении"""
    import os
    if not instance.pk:
        return False
    try:
        old_instance = Certificate.objects.get(pk=instance.pk)
    except Certificate.DoesNotExist:
        return False
    if old_instance.file and old_instance.file != instance.file:
        if os.path.isfile(old_instance.file.path):
            os.remove(old_instance.file.path)
            print(f" Удален старый файл сертификата: {old_instance.file.path}")
            