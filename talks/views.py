# talks/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import models
from django.utils import timezone

from conference_admin.views import send_status_notification
from core.models import ConferenceInfo, ImportantDate
from .forms import ReportForm, ReportResubmitForm
from .models import Report, Section
from authors.models import Author, AuthorReport, AuthorRole

import os
from django.conf import settings


def index(request):
    """Главная страница"""

    sections = Section.objects.all().order_by('name')[:3]

    # Получаем даты из core
    conference = ConferenceInfo.objects.filter(is_active=True).first()
    important_dates = ImportantDate.objects.filter(is_active=True)

    # Диагностика базы данных
    db_path = settings.DATABASES['default']['NAME']
    db_exists = os.path.exists(db_path)
    db_size = os.path.getsize(db_path) if db_exists else 0

    # Форматируем размер
    if db_size < 1024:
        size_display = f"{db_size} B"
    elif db_size < 1024 * 1024:
        size_display = f"{db_size / 1024:.1f} KB"
    else:
        size_display = f"{db_size / (1024 * 1024):.1f} MB"

    return render(request, 'index.html', {
        'sections': sections,
        'conference': conference,
        'important_dates': important_dates,
        'db_info': {
            'path': db_path,
            'exists': db_exists,
            'size': size_display,
            'size_bytes': db_size
        }
    })

def get_or_create_author_for_user(user):
    """Создать или получить автора для пользователя"""
    User = get_user_model()

    try:
        return user.author_profile
    except:
        author = Author.objects.create(
            first_name=user.first_name or 'Имя',
            last_name=user.last_name or 'Фамилия',
            middle_name=user.middle_name or '',
            email=user.email,
            user=user,
            organization=getattr(user, 'organization', '') or 'Оренбургский государственный университет',
            is_active=True
        )
        return author


@login_required
def report_create(request):
    """Создание нового доклада"""
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.status = 'draft'
            report.created_by = request.user
            report.save()

            author_profile = get_or_create_author_for_user(request.user)
            author_role = AuthorRole.objects.get(code='author')

            if not AuthorReport.objects.filter(author=author_profile, report=report).exists():
                AuthorReport.objects.create(
                    author=author_profile,
                    report=report,
                    role=author_role,
                    corresponding_author=True,
                    order=0
                )
            else:
                messages.warning(request, 'Вы уже добавлены как автор этого доклада.')

            messages.success(request, 'Доклад успешно создан! Добавьте других авторов или научных руководителей.')
            return redirect('report_edit_authors', report_id=report.id)
    else:
        form = ReportForm()

    return render(request, 'talks/report_create.html', {
        'form': form,
        'sections': Section.objects.all()
    })


@login_required
def report_edit_authors(request, report_id):
    """Редактирование авторов и научных руководителей доклада"""
    report = get_object_or_404(Report, id=report_id)

    if report.created_by != request.user:
        messages.error(request, 'У вас нет прав для редактирования этого доклада.')
        return redirect('report_list')

    if request.method == 'POST':
        if 'add_author' in request.POST:
            author_id = request.POST.get('author_id')
            role_code = request.POST.get('role_code')
            corresponding = 'corresponding' in request.POST

            try:
                author = Author.objects.get(id=author_id)
                role = AuthorRole.objects.get(code=role_code)

                existing_author_report = AuthorReport.objects.filter(
                    report=report,
                    author=author
                ).first()

                if existing_author_report:
                    messages.warning(request, f'Автор {author.get_full_name()} уже добавлен к этому докладу.')
                else:
                    max_order = AuthorReport.objects.filter(report=report).aggregate(models.Max('order'))[
                                    'order__max'] or 0

                    AuthorReport.objects.create(
                        author=author,
                        report=report,
                        role=role,
                        corresponding_author=corresponding,
                        order=max_order + 1
                    )

                    messages.success(request, f'Добавлен {role.name.lower()}: {author.get_full_name()}.')

            except Author.DoesNotExist:
                messages.error(request, 'Автор не найден.')
            except AuthorRole.DoesNotExist:
                messages.error(request, 'Роль не найдена.')

        elif 'add_new_author' in request.POST:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            middle_name = request.POST.get('middle_name', '')
            email = request.POST.get('email')
            role_code = request.POST.get('role_code')
            corresponding = 'corresponding' in request.POST

            organization = request.POST.get('organization', '')
            position = request.POST.get('position', '')
            academic_degree = request.POST.get('academic_degree', '')
            academic_title = request.POST.get('academic_title', '')
            phone = request.POST.get('phone', '')

            if not first_name or not last_name or not email:
                messages.error(request, 'Поля "Имя", "Фамилия" и "Email" обязательны для заполнения.')
            else:
                try:
                    User = get_user_model()
                    user = None
                    try:
                        user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        pass

                    author, created = Author.objects.get_or_create(
                        email=email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'middle_name': middle_name,
                            'organization': organization,
                            'position': position,
                            'academic_degree': academic_degree,
                            'academic_title': academic_title,
                            'phone': phone,
                            'user': user,
                            'is_active': True
                        }
                    )

                    if not created:
                        author.first_name = first_name
                        author.last_name = last_name
                        author.middle_name = middle_name
                        author.organization = organization
                        author.position = position
                        author.academic_degree = academic_degree
                        author.academic_title = academic_title
                        author.phone = phone
                        if user and not author.user:
                            author.user = user
                        author.save()

                    role = AuthorRole.objects.get(code=role_code)

                    existing_author_report = AuthorReport.objects.filter(
                        report=report,
                        author=author
                    ).first()

                    if existing_author_report:
                        messages.warning(request, f'Автор {author.get_full_name()} уже добавлен к этому докладу.')
                    else:
                        max_order = AuthorReport.objects.filter(report=report).aggregate(models.Max('order'))[
                                        'order__max'] or 0

                        AuthorReport.objects.create(
                            author=author,
                            report=report,
                            role=role,
                            corresponding_author=corresponding,
                            order=max_order + 1
                        )

                        messages.success(request,
                                         f'Создан и добавлен новый {role.name.lower()}: {author.get_full_name()}.')

                except AuthorRole.DoesNotExist:
                    messages.error(request, 'Роль не найдена.')
                except Exception as e:
                    messages.error(request, f'Ошибка при создании автора: {str(e)}')

        elif 'remove_author' in request.POST:
            author_report_id = request.POST.get('author_report_id')
            try:
                author_report = AuthorReport.objects.get(id=author_report_id, report=report)

                authors_count = AuthorReport.objects.filter(report=report, role__code='author').count()
                if author_report.role.code == 'author' and authors_count <= 1:
                    messages.error(request, 'Нельзя удалить единственного автора доклада.')
                else:
                    author_name = author_report.author.get_full_name()
                    author_report.delete()
                    messages.success(request, f'{author_report.role.name} {author_name} удален.')

            except AuthorReport.DoesNotExist:
                messages.error(request, 'Связь автор-доклад не найдена.')

        elif 'update_order' in request.POST:
            order_data = request.POST.get('order_data')
            if order_data:
                try:
                    order_list = json.loads(order_data)
                    for item in order_list:
                        author_report = AuthorReport.objects.get(
                            id=item['id'],
                            report=report
                        )
                        author_report.order = item['order']
                        author_report.save()

                    messages.success(request, 'Порядок авторов обновлен.')
                except (json.JSONDecodeError, KeyError):
                    messages.error(request, 'Ошибка при обновлении порядка.')
                except AuthorReport.DoesNotExist:
                    messages.error(request, 'Автор не найден.')

        elif 'update_role' in request.POST:
            author_report_id = request.POST.get('author_report_id')
            role_code = request.POST.get('role_code')
            corresponding = 'corresponding' in request.POST

            try:
                author_report = AuthorReport.objects.get(id=author_report_id, report=report)
                role = AuthorRole.objects.get(code=role_code)

                author_report.role = role
                author_report.corresponding_author = corresponding
                author_report.save()

                messages.success(request, f'Роль {author_report.author.get_full_name()} изменена на {role.name}.')

            except AuthorReport.DoesNotExist:
                messages.error(request, 'Связь авторa-доклад не найдена.')
            except AuthorRole.DoesNotExist:
                messages.error(request, 'Роль не найдена.')

        elif 'save_draft' in request.POST:
            report.status = 'draft'
            report.save()
            messages.success(request, 'Доклад сохранен как черновик.')
            return redirect('report_list')

        elif 'submit' in request.POST:
            if not AuthorReport.objects.filter(report=report, role__code='author').exists():
                messages.error(request, 'Добавьте хотя бы одного автора.')
            else:
                report.status = 'submitted'
                report.submitted_at = timezone.now()
                report.save()
                messages.success(request, 'Доклад успешно отправлен на рассмотрение!')
                return redirect('report_list')

    current_participants = AuthorReport.objects.filter(report=report).select_related('author', 'role').order_by('order')

    search_query = request.GET.get('search', '')
    organization_filter = request.GET.get('organization', '')

    added_author_ids = current_participants.values_list('author_id', flat=True)

    all_authors = get_all_available_authors(
        exclude_ids=list(added_author_ids),
        search_query=search_query,
        organization_filter=organization_filter
    )

    organizations = Author.objects.filter(is_active=True).exclude(
        organization=''
    ).values_list('organization', flat=True).distinct().order_by('organization')

    author_role = AuthorRole.objects.get(code='author')
    supervisor_role = AuthorRole.objects.get(code='supervisor')

    return render(request, 'talks/report_edit_authors.html', {
        'report': report,
        'current_participants': current_participants,
        'all_authors': all_authors,
        'author_role': author_role,
        'supervisor_role': supervisor_role,
        'search_query': search_query,
        'organization_filter': organization_filter,
        'organizations': organizations,
    })


def get_all_available_authors(exclude_ids=None, search_query='', organization_filter=''):
    """Получить всех доступных авторов"""
    if exclude_ids is None:
        exclude_ids = []

    authors = Author.objects.filter(is_active=True).exclude(id__in=exclude_ids)

    if search_query:
        authors = authors.filter(
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(middle_name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(organization__icontains=search_query)
        )

    if organization_filter:
        authors = authors.filter(organization__icontains=organization_filter)

    return authors.order_by('last_name', 'first_name')


@login_required
def report_list(request):
    """Список докладов пользователя"""
    created_reports = Report.objects.filter(created_by=request.user).order_by('-created_at')

    author_reports = Report.objects.filter(
        author_reports__author__user=request.user
    ).distinct().order_by('-created_at')

    all_reports = list(created_reports) + [
        r for r in author_reports if r not in created_reports
    ]

    return render(request, 'talks/report_list.html', {
        'reports': all_reports
    })


@login_required
def report_detail(request, report_id):
    """Детальная информация о докладе"""
    report = get_object_or_404(Report, id=report_id)

    has_access = False

    # Проверка доступа
    if report.status == 'approved':
        has_access = True
    elif report.created_by == request.user:
        has_access = True
    elif AuthorReport.objects.filter(report=report, author__user=request.user).exists():
        has_access = True
    elif request.user.is_staff:
        has_access = True

    if not has_access:
        messages.error(request, 'У вас нет доступа к этому докладу.')
        return redirect('report_list')

    # Получаем авторов, руководителей и корреспондентов
    authors = report.get_authors()
    supervisors = report.get_supervisors()
    corresponding_authors = report.get_corresponding_authors()

    # Проверяем, может ли пользователь повторно отправить доклад
    can_resubmit = report.can_be_resubmitted_by_author(request.user)

    return render(request, 'talks/report_detail.html', {
        'report': report,
        'authors': authors,
        'supervisors': supervisors,
        'corresponding_authors': corresponding_authors,
        'can_resubmit': can_resubmit,
    })


@login_required
def report_resubmit(request, report_id):
    """Повторная отправка доклада после исправления замечаний"""
    report = get_object_or_404(Report, id=report_id)

    if report.status != 'revisions_required':
        messages.error(request, 'Этот доклад не требует доработок или уже был отправлен повторно.')
        return redirect('report_detail', report_id=report.id)

    if not report.can_be_resubmitted_by_author(request.user):
        messages.error(request, 'У вас нет прав для повторной отправки этого доклада.')
        return redirect('report_detail', report_id=report.id)

    if request.method == 'POST':
        form = ReportResubmitForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            old_status = report.status
            report = form.save(commit=False)
            report.status = 'resubmitted'
            report.resubmitted_at = timezone.now()
            report.save()

            # ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ О ПОВТОРНОЙ ОТПРАВКЕ
            send_status_notification(report, old_status)

            messages.success(request, 'Доклад успешно отправлен повторно на рассмотрение!')
            return redirect('report_detail', report_id=report.id)
    else:
        form = ReportResubmitForm(instance=report)

    return render(request, 'talks/report_resubmit.html', {
        'form': form,
        'report': report
    })

@login_required
def report_edit(request, report_id):
    """Редактирование основного содержания доклада"""
    report = get_object_or_404(Report, id=report_id)

    if report.created_by != request.user:
        messages.error(request, 'У вас нет прав для редактирования этого доклада.')
        return redirect('report_list')

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'Доклад успешно обновлен.')
            return redirect('report_detail', report_id=report.id)
    else:
        form = ReportForm(instance=report)

    return render(request, 'talks/report_edit.html', {
        'form': form,
        'report': report
    })


