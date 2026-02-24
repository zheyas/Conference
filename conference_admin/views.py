# conference_admin/views.py
import json
import os
import datetime

from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import JsonResponse, FileResponse
from django.utils.html import strip_tags

from conference import settings
from .decorators import admin_required, jury_chairman_required
from .forms import (
    ReportStatusForm, CertificateForm,
    SectionForm, UserRoleForm, SearchUserForm, JuryMemberForm
)
from talks.models import Report, Certificate, Section, JuryMember
from authors.models import Author, AuthorReport
from users.models import User


@admin_required
def admin_dashboard(request):
    """Панель управления администратора"""

    # Статистика
    stats = {
        'total_reports': Report.objects.count(),
        'submitted_reports': Report.objects.filter(status='submitted').count(),
        'under_review': Report.objects.filter(status='review').count(),
        'approved_reports': Report.objects.filter(status='approved').count(),
        'revisions_required': Report.objects.filter(status='revisions_required').count(),
        'rejected_reports': Report.objects.filter(status='rejected').count(),
        'total_authors': Author.objects.count(),
        'total_certificates': Certificate.objects.count(),
        'total_sections': Section.objects.count(),
    }

    # Последние поданные доклады
    recent_reports = Report.objects.filter(
        status__in=['submitted', 'review']
    ).order_by('-submitted_at')[:10]

    # Доклады, требующие внимания
    attention_reports = Report.objects.filter(
        Q(status='submitted') |
        Q(status='revisions_required')
    ).distinct()[:5]

    return render(request, 'conference_admin/dashboard.html', {
        'stats': stats,
        'recent_reports': recent_reports,
        'attention_reports': attention_reports,
    })


@admin_required
def report_list_admin(request):
    """Список всех докладов для администратора"""

    status_filter = request.GET.get('status', 'all')
    section_filter = request.GET.get('section', 'all')
    search_query = request.GET.get('search', '')

    reports = Report.objects.select_related('section').prefetch_related(
        'author_reports__author'
    ).order_by('-created_at')

    # Применяем фильтры
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)

    if section_filter != 'all':
        reports = reports.filter(section_id=section_filter)

    if search_query:
        reports = reports.filter(
            Q(title__icontains=search_query) |
            Q(abstract__icontains=search_query) |
            Q(author_reports__author__first_name__icontains=search_query) |
            Q(author_reports__author__last_name__icontains=search_query)
        ).distinct()

    # Пагинация
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sections = Section.objects.all()

    return render(request, 'conference_admin/report_list.html', {
        'page_obj': page_obj,
        'sections': sections,
        'status_filter': status_filter,
        'section_filter': section_filter,
        'search_query': search_query,
    })


@admin_required
def report_detail_admin(request, report_id):
    """Детальная информация о докладе для администратора"""

    report = get_object_or_404(Report, id=report_id)
    authors = AuthorReport.objects.filter(report=report).select_related('author', 'role').order_by('order')
    certificates = Certificate.objects.filter(report=report).select_related('author')

    if request.method == 'POST':
        if 'change_status' in request.POST:
            status_form = ReportStatusForm(request.POST, instance=report)
            if status_form.is_valid():
                old_status = report.status
                report = status_form.save()

                # Устанавливаем время рассмотрения
                if report.status in ['approved', 'rejected', 'revisions_required']:
                    report.reviewed_at = timezone.now()

                report.save()

                # ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ ПРИ ЛЮБОМ ИЗМЕНЕНИИ СТАТУСА
                send_status_notification(report, old_status)

                messages.success(
                    request,
                    f'Статус доклада изменен с "{old_status}" на "{report.get_status_display()}". '
                    f'Уведомления отправлены авторам.'
                )

                return redirect('conference_admin:report_detail', report_id=report.id)
    else:
        status_form = ReportStatusForm(instance=report)

    return render(request, 'conference_admin/report_detail.html', {
        'report': report,
        'authors': authors,
        'certificates': certificates,
        'status_form': status_form,
    })

@admin_required
def manage_certificates(request, report_id):
    """Управление грамотами/сертификатами для доклада"""

    report = get_object_or_404(Report, id=report_id)
    authors = AuthorReport.objects.filter(
        report=report
    ).select_related('author')

    certificates = Certificate.objects.filter(
        report=report
    ).select_related('author')

    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.report = report
            certificate.issued_by = request.user
            certificate.save()

            messages.success(request, 'Грамота/сертификат успешно добавлен.')
            return redirect('conference_admin:manage_certificates', report_id=report.id)
    else:
        form = CertificateForm()
        # Ограничиваем выбор авторов только авторами этого доклада
        form.fields['author'].queryset = Author.objects.filter(
            report_authorships__report=report
        ).distinct()

    return render(request, 'conference_admin/manage_certificates.html', {
        'report': report,
        'authors': authors,
        'certificates': certificates,
        'form': form,
    })


@admin_required
def delete_certificate(request, certificate_id):
    """Удаление грамоты/сертификата"""

    certificate = get_object_or_404(Certificate, id=certificate_id)
    report_id = certificate.report.id

    if request.method == 'POST':
        certificate.delete()
        messages.success(request, 'Грамота/сертификат удален.')

    return redirect('conference_admin:manage_certificates', report_id=report_id)


@admin_required
def manage_sections(request):
    """Управление секциями конференции"""

    sections = Section.objects.all().order_by('-created_at')
    all_users = User.objects.filter(is_active=True).order_by('last_name', 'first_name')

    # Получаем статистику для отображения в шаблоне
    total_reports = Report.objects.count()
    total_jury_members = JuryMember.objects.count()

    if request.method == 'POST':
        # ОБРАБОТКА ДОБАВЛЕНИЯ СЕКЦИИ
        if 'add_section' in request.POST:
            form = SectionForm(request.POST, request.FILES)
            if form.is_valid():
                section = form.save()
                messages.success(request, f'Секция "{section.name}" успешно создана.')
                return redirect('conference_admin:manage_sections')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
                # Сохраняем форму с ошибками для отображения в шаблоне
                context = {
                    'sections': sections,
                    'form': form,
                    'all_users': all_users,
                    'total_reports': total_reports,
                    'total_jury_members': total_jury_members,
                }
                return render(request, 'conference_admin/manage_sections.html', context)

        # ОБРАБОТКА РЕДАКТИРОВАНИЯ СЕКЦИИ
        elif 'edit_section' in request.POST:
            section_id = request.POST.get('section_id')
            try:
                section = get_object_or_404(Section, id=section_id)
                form = SectionForm(request.POST, request.FILES, instance=section)

                if form.is_valid():
                    section = form.save()
                    messages.success(request, f'Секция "{section.name}" успешно обновлена.')
                    return redirect('conference_admin:manage_sections')
                else:
                    messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
                    # Сохраняем форму с ошибками
                    context = {
                        'sections': sections,
                        'form': form,
                        'all_users': all_users,
                        'total_reports': total_reports,
                        'total_jury_members': total_jury_members,
                    }
                    return render(request, 'conference_admin/manage_sections.html', context)
            except Exception as e:
                messages.error(request, f'Ошибка при редактировании: {str(e)}')
                return redirect('conference_admin:manage_sections')

        # ОБРАБОТКА УДАЛЕНИЯ СЕКЦИИ
        elif 'delete_section' in request.POST:
            section_id = request.POST.get('section_id')
            try:
                section = get_object_or_404(Section, id=section_id)

                if section.reports.exists():
                    messages.error(
                        request,
                        f'Нельзя удалить секцию "{section.name}", в которой есть доклады. '
                        'Сначала переместите доклады в другую секцию.'
                    )
                else:
                    section_name = section.name
                    section.delete()
                    messages.success(request, f'Секция "{section_name}" успешно удалена.')

            except Exception as e:
                messages.error(request, f'Ошибка при удалении: {str(e)}')

            return redirect('conference_admin:manage_sections')

    else:
        # GET запрос - показываем пустую форму
        form = SectionForm()

    return render(request, 'conference_admin/manage_sections.html', {
        'sections': sections,
        'form': form,
        'all_users': all_users,
        'total_reports': total_reports,
        'total_jury_members': total_jury_members,
    })


@admin_required
def edit_section(request, section_id):
    """Редактирование секции (отдельная страница)"""
    section = get_object_or_404(Section, id=section_id)
    all_users = User.objects.filter(is_active=True).order_by('last_name', 'first_name')

    if request.method == 'POST':
        form = SectionForm(request.POST, request.FILES, instance=section)
        if form.is_valid():
            section = form.save()
            messages.success(request, f'Секция "{section.name}" успешно обновлена.')
            return redirect('conference_admin:manage_sections')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = SectionForm(instance=section)

    return render(request, 'conference_admin/edit_section.html', {
        'section': section,
        'form': form,
        'all_users': all_users,
    })


@admin_required
def author_list_admin(request):
    """Список всех авторов для администратора"""

    search_query = request.GET.get('search', '')

    authors = Author.objects.all().order_by('last_name', 'first_name')

    if search_query:
        authors = authors.filter(
            Q(last_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(organization__icontains=search_query)
        )

    # Добавляем статистику по каждому автору
    for author in authors:
        author.report_count = author.reports.count()
        author.certificate_count = author.certificates.count()

    # Пагинация
    paginator = Paginator(authors, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'conference_admin/author_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })


@admin_required
def user_list_admin(request):
    """Список всех пользователей системы"""

    role_filter = request.GET.get('role', 'all')
    search_query = request.GET.get('search', '')

    users = User.objects.all().order_by('last_name', 'first_name')

    # Применяем фильтры
    if role_filter != 'all':
        users = users.filter(role=role_filter)

    if search_query:
        users = users.filter(
            Q(last_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(organization__icontains=search_query)
        )

    # Пагинация
    paginator = Paginator(users, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'conference_admin/user_list.html', {
        'page_obj': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'roles': User.Role.choices,
    })


@admin_required
def change_user_role(request, user_id):
    """Изменение роли пользователя"""

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserRoleForm(request.POST)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            old_role_display = user.get_role_display()
            user.role = new_role
            user.save()

            messages.success(
                request,
                f'Роль пользователя {user.get_full_name()} изменена '
                f'с "{old_role_display}" на "{user.get_role_display()}"'
            )
            return redirect('conference_admin:user_list')
    else:
        form = UserRoleForm(initial={'role': user.role})

    return render(request, 'conference_admin/change_user_role.html', {
        'form': form,
        'user': user,
    })


@admin_required
def get_section_data(request, section_id):
    """Получение данных секции для редактирования (JSON API)"""
    section = get_object_or_404(Section, id=section_id)

    data = {
        'name': section.name,
        'description': section.description,
        'date': section.date.strftime('%Y-%m-%d'),
        'time': section.time.strftime('%H:%M'),
        'location': section.location,
        'jury_chairman': str(section.jury_chairman.id) if section.jury_chairman else None,
        'icon_url': section.icon.url if section.icon else None,
    }

    return JsonResponse(data)


@admin_required
def statistics(request):
    """Статистика конференции"""

    # Общая статистика
    total_reports = Report.objects.count()

    reports_by_status = Report.objects.values(
        'status'
    ).annotate(
        count=Count('id')
    ).order_by('status')

    reports_by_section = Report.objects.filter(
        section__isnull=False
    ).values(
        'section__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    # Топ авторов
    top_authors = Author.objects.annotate(
        report_count=Count('reports'),
        certificate_count=Count('certificates')
    ).order_by('-report_count')[:10]

    # Статистика по месяцам
    monthly_stats = []
    try:
        monthly_stats = Report.objects.extra(
            select={'month': "strftime('%Y-%m', created_at)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
    except:
        pass

    return render(request, 'conference_admin/statistics.html', {
        'total_reports': total_reports,
        'reports_by_status': reports_by_status,
        'reports_by_section': reports_by_section,
        'top_authors': top_authors,
        'monthly_stats': list(monthly_stats),
    })


@admin_required
def statistics_api(request):
    """API для статистики (JSON)"""

    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    daily_stats = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')

        reports_count = Report.objects.filter(
            created_at__date=date.date()
        ).count()

        daily_stats.append({
            'date': date_str,
            'reports': reports_count,
        })

    return JsonResponse({
        'daily_stats': daily_stats,
        'total_reports': Report.objects.count(),
        'total_authors': Author.objects.count(),
    })


@login_required
def jury_chairman_dashboard(request):
    """Панель управления председателя жюри"""

    # Получаем все секции, где пользователь является председателем
    sections = Section.objects.filter(jury_chairman=request.user)

    if not sections.exists():
        messages.info(request, 'Вы не являетесь председателем жюри ни одной секции.')
        return redirect('index')

    # Статистика для председателя
    reports_by_section = []

    for section in sections:
        section_stats = {
            'section_name': section.name,
            'total_reports': section.reports.count(),
            'submitted_reports': section.reports.filter(status='submitted').count(),
            'under_review': section.reports.filter(status='review').count(),
            'approved_reports': section.reports.filter(status='approved').count(),
            'revisions_required': section.reports.filter(status='revisions_required').count(),
        }
        reports_by_section.append(section_stats)

    # Последние доклады в секциях пользователя
    recent_reports = Report.objects.filter(
        section__in=sections
    ).select_related('section').order_by('-created_at')[:10]

    return render(request, 'conference_admin/jury_chairman_dashboard.html', {
        'sections': sections,
        'reports_by_section': reports_by_section,
        'recent_reports': recent_reports,
    })


@jury_chairman_required
def jury_section_reports(request, section_id):
    """Доклады в секции председателя жюри"""

    section = get_object_or_404(Section, id=section_id)

    # Проверка, что пользователь действительно председатель этой секции
    if section.jury_chairman != request.user:
        messages.error(request, 'У вас нет доступа к этой секции.')
        return redirect('conference_admin:jury_chairman_dashboard')

    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    reports = section.reports.all().select_related('section').prefetch_related(
        'author_reports__author'
    ).order_by('-created_at')

    # Применяем фильтры
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)

    if search_query:
        reports = reports.filter(
            Q(title__icontains=search_query) |
            Q(abstract__icontains=search_query)
        )

    # Пагинация
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'conference_admin/jury_section_reports.html', {
        'section': section,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    })


@admin_required
def manage_section_jury(request, section_id):
    """Управление членами жюри секции"""

    section = get_object_or_404(Section, id=section_id)
    jury_members = section.jury_members_list.all().order_by('order')

    # Форма поиска пользователей
    search_form = SearchUserForm(request.GET or None)
    users = []

    if search_form.is_valid() and search_form.cleaned_data.get('search'):
        search_term = search_form.cleaned_data['search']
        users = User.objects.filter(
            Q(last_name__icontains=search_term) |
            Q(first_name__icontains=search_term) |
            Q(email__icontains=search_term)
        ).exclude(
            id__in=jury_members.filter(user__isnull=False).values('user_id')
        ).order_by('last_name', 'first_name')[:20]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_jury_member':
            form = JuryMemberForm(request.POST)
            if form.is_valid():
                jury_member = form.save(commit=False)
                jury_member.section = section

                if jury_member.user:
                    jury_member.last_name = jury_member.user.last_name
                    jury_member.first_name = jury_member.user.first_name
                    jury_member.middle_name = jury_member.user.middle_name
                    jury_member.organization = jury_member.user.organization
                    jury_member.position = jury_member.user.position
                    jury_member.academic_degree = jury_member.user.academic_degree
                    jury_member.academic_title = jury_member.user.academic_title
                    jury_member.email = jury_member.user.email
                    jury_member.phone = jury_member.user.phone

                jury_member.save()
                messages.success(request, 'Член жюри добавлен.')
                return redirect('conference_admin:manage_section_jury', section_id=section_id)

        elif action == 'delete_jury_member':
            member_id = request.POST.get('member_id')
            try:
                member = JuryMember.objects.get(id=member_id, section=section)
                member.delete()
                messages.success(request, 'Член жюри удален.')
            except JuryMember.DoesNotExist:
                messages.error(request, 'Член жюри не найден.')
            return redirect('conference_admin:manage_section_jury', section_id=section_id)

        elif action == 'reorder_jury_members':
            order_data = request.POST.get('order_data', '[]')
            try:
                order_list = json.loads(order_data)
                for item in order_list:
                    member = JuryMember.objects.get(id=item['id'], section=section)
                    member.order = item['order']
                    member.save()
                messages.success(request, 'Порядок сохранен.')
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении порядка: {str(e)}')
            return redirect('conference_admin:manage_section_jury', section_id=section_id)

    else:
        form = JuryMemberForm()

    return render(request, 'conference_admin/manage_section_jury.html', {
        'section': section,
        'jury_members': jury_members,
        'form': form,
        'search_form': search_form,
        'users': users,
    })


@admin_required
def add_user_to_jury(request, section_id, user_id):
    """Быстрое добавление пользователя в члены жюри"""

    section = get_object_or_404(Section, id=section_id)
    user = get_object_or_404(User, id=user_id)

    if JuryMember.objects.filter(section=section, user=user).exists():
        messages.warning(request, f'{user.get_full_name()} уже является членом жюри этой секции.')
    else:
        # Создаем члена жюри
        jury_member = JuryMember(
            section=section,
            user=user,
            last_name=user.last_name,
            first_name=user.first_name,
            middle_name=user.middle_name,
            organization=user.organization,
            position=user.position,
            academic_degree=user.academic_degree,
            academic_title=user.academic_title,
            email=user.email,
            phone=user.phone,
            order=section.jury_members_list.count() + 1
        )
        jury_member.save()
        messages.success(request, f'{user.get_full_name()} добавлен в члены жюри.')

    return redirect('conference_admin:manage_section_jury', section_id=section_id)


@admin_required
def download_database(request):
    """Скачивание базы данных SQLite"""

    # Путь к файлу базы данных
    db_path = settings.DATABASES['default']['NAME']

    # Проверяем, существует ли файл
    if not os.path.exists(db_path):
        messages.error(request, 'Файл базы данных не найден')
        return redirect('conference_admin:dashboard')

    # Создаем имя файла с датой
    today = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"conference_db_backup_{today}.sqlite3"

    # Открываем файл для чтения в бинарном режиме
    response = FileResponse(
        open(db_path, 'rb'),
        as_attachment=True,
        filename=filename
    )

    # Добавляем заголовки для правильной обработки
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Length'] = os.path.getsize(db_path)

    return response


def send_status_notification(report, old_status=None):
    """
    Отправляет уведомление об изменении статуса доклада всем авторам

    Args:
        report: объект доклада
        old_status: предыдущий статус (опционально)
    """

    # Получаем всех авторов доклада
    authors = report.author_reports.all().select_related('author')

    # Если авторов нет, выходим
    if not authors:
        print(f"⚠️ Нет авторов для уведомления по докладу {report.id}")
        return

    # Определяем статус и тему письма
    status_display = report.get_status_display()

    # Настраиваем тему и шаблон в зависимости от статуса
    status_templates = {
        'approved': {
            'subject': f' Доклад принят - {settings.SITE_NAME}',
            'template': 'emails/report_approved.html',
            'icon': '✅'
        },
        'rejected': {
            'subject': f' Доклад отклонен - {settings.SITE_NAME}',
            'template': 'emails/report_rejected.html',
            'icon': '❌'
        },
        'revisions_required': {
            'subject': f' Требуются доработки - {settings.SITE_NAME}',
            'template': 'emails/revision_required.html',
            'icon': '✏️'
        },
        'submitted': {
            'subject': f' Доклад подан - {settings.SITE_NAME}',
            'template': 'emails/report_submitted.html',
            'icon': '📤'
        },
        'review': {
            'subject': f' Доклад на рассмотрении - {settings.SITE_NAME}',
            'template': 'emails/report_review.html',
            'icon': '🔍'
        },
    }

    # Выбираем шаблон для текущего статуса
    status_info = status_templates.get(report.status, {
        'subject': f' Статус доклада изменен - {settings.SITE_NAME}',
        'template': 'emails/status_changed.html',
        'icon': '📋'
    })

    subject = status_info['subject']
    template_name = status_info['template']

    # Контекст для шаблона
    context = {
        'report': report,
        'conference_name': settings.SITE_NAME,
        'conference_dates': '15-17 мая 2026',
        'site_url': settings.SITE_URL,
        'status_display': status_display,
        'status_icon': status_info['icon'],
        'old_status': old_status,
        'admin_comment': report.admin_comment,
        'current_year': timezone.now().year,
    }

    # Для каждого автора отправляем письмо
    successful_sends = 0
    failed_sends = 0

    for author_report in authors:
        author = author_report.author

        # Пропускаем авторов без email
        if not author.email:
            print(f"! У автора {author.get_full_name()} нет email")
            continue

        # Формируем персонализированное приветствие
        context['author_name'] = author.get_full_name()
        context['author_email'] = author.email

        try:
            # Рендерим HTML-шаблон письма
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)

            # Добавляем автоматическую подпись
            plain_message += f"""

---
 Это автоматическое письмо, созданное системой управления конференцией {settings.SITE_NAME}.
Пожалуйста, не отвечайте на него. Для связи используйте: {settings.DEFAULT_FROM_EMAIL}

© {timezone.now().year} {settings.SITE_NAME} | Оренбургский государственный университет"""

            html_message += f"""
<hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
<p style="color: #666; font-size: 12px; text-align: center;">
     Это автоматическое письмо, созданное системой управления конференцией <strong>{settings.SITE_NAME}</strong>.<br>
    Пожалуйста, не отвечайте на него. Для связи используйте: <a href="mailto:{settings.DEFAULT_FROM_EMAIL}">{settings.DEFAULT_FROM_EMAIL}</a>
</p>
<p style="color: #999; font-size: 11px; text-align: center;">
    © {timezone.now().year} {settings.SITE_NAME} | Оренбургский государственный университет
</p>"""

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [author.email],
                html_message=html_message,
                fail_silently=False,
            )
            successful_sends += 1
            print(f"✅ Уведомление отправлено {author.email}")

        except Exception as e:
            failed_sends += 1
            print(f"❌ Ошибка отправки {author.email}: {e}")
    print(f"🔍 Функция send_status_notification вызвана для доклада {report.id}")
    print(f"   Статус: {old_status} -> {report.status}")
    print(f"   Авторы: {report.author_reports.count()}")
    # Логируем результат
    print(f" Отправлено уведомлений: {successful_sends}, ошибок: {failed_sends}")

    return successful_sends, failed_sends
