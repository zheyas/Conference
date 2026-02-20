# talks/templatetags/custom_filters.py
from django import template
import os
register = template.Library()


# Простой тестовый фильтр для проверки
@register.filter
def test_filter(value):
    return f"Test: {value}"


# Удаляем или комментируем все фильтры, связанные с рецензиями
# @register.filter
# def get_reviews_for_user(report, user):
#     """Получить рецензии для пользователя - УДАЛЕНО"""
#     return None

# @register.filter
# def has_reviews_for_user(report, user):
#     """Проверить, есть ли рецензии для пользователя - УДАЛЕНО"""
#     return False


# Оставляем только полезные фильтры, не связанные с рецензиями
@register.filter
def get_approved_count(reports):
    """Получить количество одобренных докладов"""
    if not reports:
        return 0
    return sum(1 for report in reports if report.status == "approved")


@register.filter
def file_extension(value):
    """Возвращает расширение файла в верхнем регистре"""
    if value:
        return os.path.splitext(value.name)[1][1:].upper()
    return ''

# Добавляем полезные фильтры для работы со статусами
@register.filter
def status_class(status):
    """Возвращает CSS класс для статуса доклада"""
    status_classes = {
        'draft': 'badge-draft',
        'submitted': 'badge-submitted',
        'review': 'badge-review',
        'approved': 'badge-approved',
        'rejected': 'badge-rejected',
        'revisions_required': 'badge-revisions',
        'resubmitted': 'badge-resubmitted',
    }
    return status_classes.get(status, 'badge-default')


@register.filter
def status_icon(status):
    """Возвращает иконку для статуса доклада"""
    status_icons = {
        'draft': '📝',
        'submitted': '⏳',
        'review': '🔍',
        'approved': '✅',
        'rejected': '❌',
        'revisions_required': '⚠️',
        'resubmitted': '🔄',
    }
    return status_icons.get(status, '📄')


@register.filter
def has_admin_comment(report):
    """Проверяет, есть ли комментарий администратора"""
    return bool(report.admin_comment)


@register.filter
def get_authors_short(report, limit=3):
    """Возвращает краткий список авторов"""
    authors = report.get_authors()[:limit]
    names = [author.author.get_short_name() for author in authors]
    result = ', '.join(names)

    total = report.get_authors().count()
    if total > limit:
        result += f' и ещё {total - limit}'

    return result
