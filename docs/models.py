import os
from django.db import models
from django.dispatch import receiver


def document_upload_path(instance, filename):
    """Сохранение в папку file"""
    return os.path.join('file', filename)


class Document(models.Model):
    """Простая модель для документов"""

    title = models.CharField(
        max_length=200,
        verbose_name='Название документа'
    )

    file = models.FileField(
        upload_to=document_upload_path,
        verbose_name='Файл'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    def get_file_size(self):
        """Размер файла в читаемом формате"""
        if self.file and hasattr(self.file, 'size'):
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return '0 B'

    def delete(self, *args, **kwargs):
        """Переопределяем метод delete для удаления файла с диска"""
        # Сохраняем путь к файлу перед удалением
        file_path = None
        if self.file:
            file_path = self.file.path

        # Вызываем оригинальный метод delete
        super().delete(*args, **kwargs)

        # Удаляем файл после удаления записи
        if file_path and os.path.isfile(file_path):
            os.remove(file_path)
            print(f" Файл {file_path} удален с диска")


# Сигнал для удаления файла при удалении записи
@receiver(models.signals.post_delete, sender=Document)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Удаляет файл с диска при удалении записи из базы данных
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
            print(f" Файл {instance.file.path} удален с диска (сигнал)")


# Сигнал для удаления старого файла при обновлении
@receiver(models.signals.pre_save, sender=Document)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Удаляет старый файл с диска при обновлении записи (замене файла)
    """
    if not instance.pk:
        return False

    try:
        old_instance = Document.objects.get(pk=instance.pk)
        old_file = old_instance.file
    except Document.DoesNotExist:
        return False

    # Проверяем, изменился ли файл
    new_file = instance.file
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
            print(f" Старый файл {old_file.path} удален при обновлении")
