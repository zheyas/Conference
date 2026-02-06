from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from talks.models import Section


def admin_required(view_func):
    """
    Декоратор для проверки прав администратора конференции.
    Доступ имеют:
    1. Суперпользователи
    2. Пользователи с ролью ADMIN, MODERATOR, SUPER_ADMIN
    3. Председатели жюри для своей секции (если передается section_id в URL)
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login') + f'?next={request.path}')

        # Суперпользователи и администраторы всегда имеют доступ
        if request.user.is_superuser or request.user.is_conference_admin:
            return view_func(request, *args, **kwargs)

        # Проверяем, является ли пользователь председателем жюри для определенной секции
        section_id = kwargs.get('section_id') or request.GET.get('section_id')

        if section_id:
            try:
                section = Section.objects.get(id=section_id)
                if section.jury_chairman == request.user:
                    return view_func(request, *args, **kwargs)
                elif request.user in section.jury_members.all():
                    # Можно также дать ограниченные права членам жюри
                    return view_func(request, *args, **kwargs)
            except Section.DoesNotExist:
                pass

        messages.error(request, 'У вас нет прав доступа к этой странице.')
        return redirect('index')

    return _wrapped_view


# Добавьте в conference_admin/decorators.py

def jury_chairman_required(view_func):
    """
    Декоратор для проверки прав председателя жюри секции.
    Доступ имеют председатели жюри только для своей секции.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login') + f'?next={request.path}')

        # Суперпользователи и администраторы всегда имеют доступ
        if request.user.is_superuser or request.user.is_conference_admin:
            return view_func(request, *args, **kwargs)

        # Получаем section_id из URL или параметров
        section_id = kwargs.get('section_id') or request.GET.get('section_id')

        if not section_id:
            messages.error(request, 'Не указана секция.')
            return redirect('index')

        try:
            section = Section.objects.get(id=section_id)

            # Проверяем, является ли пользователь председателем этой секции
            if section.jury_chairman == request.user:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request,
                    f'Вы не являетесь председателем жюри секции "{section.name}".'
                )
                return redirect('index')

        except Section.DoesNotExist:
            messages.error(request, 'Секция не найдена.')
            return redirect('index')

    return _wrapped_view
