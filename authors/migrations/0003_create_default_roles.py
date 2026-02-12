# authors/migrations/0003_create_default_roles.py
from django.db import migrations


def create_default_roles(apps, schema_editor):
    AuthorRole = apps.get_model('authors', 'AuthorRole')

    # Создаем роли по умолчанию, если они еще не существуют
    AuthorRole.objects.get_or_create(
        code='author',
        defaults={
            'name': 'Автор',
            'description': 'Основной автор работы',
            'order': 1
        }
    )

    AuthorRole.objects.get_or_create(
        code='supervisor',
        defaults={
            'name': 'Научный руководитель',
            'description': 'Научный руководитель работы',
            'order': 2
        }
    )


def reverse_create_default_roles(apps, schema_editor):
    AuthorRole = apps.get_model('authors', 'AuthorRole')
    AuthorRole.objects.filter(code__in=['author', 'supervisor']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('authors', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_roles, reverse_create_default_roles),
    ]