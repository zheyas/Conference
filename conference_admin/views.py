import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse

from .decorators import admin_required, jury_chairman_required
from .forms import (
    ReportStatusForm, ReviewForm, CertificateForm,
    SectionForm, UserRoleForm, SearchUserForm, JuryMemberForm
)
from talks.models import Report, Review, Certificate, Section, JuryMember
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
        'rejected_reports': Report.objects.filter(status='rejected').count(),
        'total_authors': Author.objects.count(),
        'pending_reviews': Review.objects.filter(is_confirmed=False).count(),
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
        Q(reviews__is_confirmed=False)
    ).distinct()[:5]

    # Последние рецензии
    recent_reviews = Review.objects.select_related(
        'report', 'reviewer'
    ).order_by('-created_at')[:5]

    return render(request, 'conference_admin/dashboard.html', {
        'stats': stats,
        'recent_reports': recent_reports,
        'attention_reports': attention_reports,
        'recent_reviews': recent_reviews,
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

    report = get_object_or_404(
        Report.objects.select_related('section', 'created_by'),
        id=report_id
    )

    authors = AuthorReport.objects.filter(
        report=report
    ).select_related('author', 'role').order_by('order')

    reviews = Review.objects.filter(
        report=report
    ).select_related('reviewer')

    certificates = Certificate.objects.filter(
        report=report
    ).select_related('author')

    # Форма для изменения статуса
    status_form = ReportStatusForm(initial={'status': report.status})

    if request.method == 'POST':
        if 'change_status' in request.POST:
            status_form = ReportStatusForm(request.POST)
            if status_form.is_valid():
                new_status = status_form.cleaned_data['status']
                comment = status_form.cleaned_data['comment']

                # Сохраняем старый статус для сообщения
                old_status_display = report.get_status_display()

                # Обновляем статус
                report.status = new_status
                report.reviewed_at = timezone.now()
                report.save()

                messages.success(
                    request,
                    f'Статус доклада изменен с "{old_status_display}" '
                    f'на "{report.get_status_display()}"'
                )

                if comment:
                    messages.info(request, f'Комментарий для автора: {comment}')

                return redirect('conference_admin:report_detail', report_id=report.id)

    return render(request, 'conference_admin/report_detail.html', {
        'report': report,
        'authors': authors,
        'reviews': reviews,
        'certificates': certificates,
        'status_form': status_form,
    })


@admin_required
def create_review(request, report_id):
    """Создание рецензии на доклад"""

    report = get_object_or_404(Report, id=report_id)

    # Проверяем, не оставлял ли уже этот рецензент рецензию
    existing_review = Review.objects.filter(
        report=report,
        reviewer=request.user
    ).first()

    if existing_review:
        messages.info(request, 'Вы уже оставили рецензию на этот доклад.')
        return redirect('conference_admin:report_detail', report_id=report.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.report = report
            review.reviewer = request.user
            review.submitted_at = timezone.now()
            review.save()

            # Обновляем статус доклада, если он был "submitted"
            if report.status == 'submitted':
                report.status = 'review'
                report.save()

            messages.success(request, 'Рецензия успешно добавлена.')
            return redirect('conference_admin:report_detail', report_id=report.id)
    else:
        form = ReviewForm()

    return render(request, 'conference_admin/create_review.html', {
        'form': form,
        'report': report,
    })


@admin_required
def edit_review(request, review_id):
    """Редактирование рецензии"""

    review = get_object_or_404(Review, id=review_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рецензия успешно обновлена.')
            return redirect('conference_admin:report_detail', report_id=review.report.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'conference_admin/edit_review.html', {
        'form': form,
        'review': review,
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

    # Для дебаггинга
    print(f"\n=== Управление секциями ===")
    print(f"Метод запроса: {request.method}")
    print(f"Пользователь: {request.user.email if request.user.is_authenticated else 'Не аутентифицирован'}")

    sections = Section.objects.all().order_by('name')
    print(f"Найдено секций в БД: {sections.count()}")

    from users.models import User
    all_users = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
    print(f"Найдено пользователей для выбора председателя: {all_users.count()}")

    if request.method == 'POST':
        print(f"\nPOST данные:")
        for key, value in request.POST.items():
            print(f"  {key}: {value}")

        if 'add_section' in request.POST:
            print("\n=== Попытка создания секции ===")
            form = SectionForm(request.POST, request.FILES)
            print(f"Форма создана: {form}")
            print(f"Данные формы: {form.data}")
            print(f"Файлы: {request.FILES}")

            if form.is_valid():
                print("✓ Форма валидна")
                try:
                    section = form.save()
                    print(f"✓ Секция сохранена: ID={section.id}, Название='{section.name}'")
                    messages.success(request, f'Секция "{section.name}" успешно создана.')
                    return redirect('conference_admin:manage_sections')
                except Exception as e:
                    print(f"✗ Ошибка при сохранении: {str(e)}")
                    messages.error(request, f'Ошибка при сохранении секции: {str(e)}')
            else:
                print("✗ Форма не валидна")
                print(f"Ошибки формы: {form.errors}")
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')

        elif 'edit_section' in request.POST:
            print("\n=== Попытка редактирования секции ===")
            section_id = request.POST.get('section_id')
            print(f"ID секции для редактирования: {section_id}")

            try:
                section = get_object_or_404(Section, id=section_id)
                form = SectionForm(request.POST, request.FILES, instance=section)

                if form.is_valid():
                    section = form.save()
                    print(f"✓ Секция обновлена: ID={section.id}, Название='{section.name}'")
                    messages.success(request, f'Секция "{section.name}" успешно обновлена.')
                    return redirect('conference_admin:manage_sections')
                else:
                    print(f"✗ Форма редактирования не валидна: {form.errors}")
                    messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
            except Exception as e:
                print(f"✗ Ошибка при редактировании: {str(e)}")
                messages.error(request, f'Ошибка при редактировании: {str(e)}')

        elif 'delete_section' in request.POST:
            print("\n=== Попытка удаления секции ===")
            section_id = request.POST.get('section_id')
            print(f"ID секции для удаления: {section_id}")

            try:
                section = get_object_or_404(Section, id=section_id)
                print(f"Найдена секция: '{section.name}'")

                # Проверяем, есть ли доклады в этой секции
                if section.reports.exists():
                    print(f"✗ В секции есть доклады ({section.reports.count()})")
                    messages.error(
                        request,
                        f'Нельзя удалить секцию "{section.name}", в которой есть доклады. '
                        'Сначала переместите доклады в другую секцию.'
                    )
                else:
                    section_name = section.name
                    section.delete()
                    print(f"✓ Секция '{section_name}' удалена")
                    messages.success(request, f'Секция "{section_name}" успешно удалена.')

            except Exception as e:
                print(f"✗ Ошибка при удалении: {str(e)}")
                messages.error(request, f'Ошибка при удалении: {str(e)}')

            return redirect('conference_admin:manage_sections')
    else:
        print("\n=== GET запрос ===")
        form = SectionForm()
        print(f"Форма для GET запроса создана: {form}")

    print(f"Передаем в шаблон: {sections.count()} секций, форма с {len(form.fields)} полями")
    print("====================\n")

    return render(request, 'conference_admin/manage_sections.html', {
        'sections': sections,
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
        'jury_members': [str(member.id) for member in section.jury_members.all()],
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

    # Статистика по рецензиям
    total_reviews = Review.objects.count()
    confirmed_reviews = Review.objects.filter(is_confirmed=True).count()

    # Вычисляем средний балл в Python, так как total_score - это свойство
    reviews = Review.objects.all()
    if reviews.exists():
        # Создаем список всех total_score
        total_scores = []
        for review in reviews:
            total_scores.append(review.total_score)
        avg_score = sum(total_scores) / len(total_scores)
    else:
        avg_score = 0

    reviews_stats = {
        'total': total_reviews,
        'avg_score': round(avg_score, 1),
        'confirmed': confirmed_reviews,
    }

    # Топ авторов
    top_authors = Author.objects.annotate(
        report_count=Count('reports'),
        certificate_count=Count('certificates')
    ).order_by('-report_count')[:10]

    # Статистика по месяцам (только если используете SQLite)
    monthly_stats = []
    try:
        monthly_stats = Report.objects.extra(
            select={'month': "strftime('%Y-%m', created_at)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
    except:
        # Для других баз данных или если возникла ошибка
        pass

    return render(request, 'conference_admin/statistics.html', {
        'total_reports': total_reports,
        'reports_by_status': reports_by_status,
        'reports_by_section': reports_by_section,
        'reviews_stats': reviews_stats,
        'top_authors': top_authors,
        'monthly_stats': list(monthly_stats),
    })


@admin_required
def statistics_api(request):
    """API для статистики (JSON)"""

    # Статистика по дням (последние 30 дней)
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

    # Вычисляем средний балл для API
    reviews = Review.objects.all()
    if reviews.exists():
        total_scores = []
        for review in reviews:
            total_scores.append(review.total_score)
        avg_review_score = sum(total_scores) / len(total_scores)
    else:
        avg_review_score = 0

    return JsonResponse({
        'daily_stats': daily_stats,
        'total_reports': Report.objects.count(),
        'total_authors': Author.objects.count(),
        'total_reviews': Review.objects.count(),
        'avg_review_score': round(avg_review_score, 1),
    })

@admin_required
def statistics_api(request):
    """API для статистики (JSON)"""

    # Статистика по дням (последние 30 дней)
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
        'total_reviews': Review.objects.count(),
        'avg_review_score': Review.objects.aggregate(
            avg=Avg('total_score')
        )['avg'] or 0,
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
    stats = {}
    reports_by_section = []

    for section in sections:
        section_stats = {
            'section_name': section.name,
            'total_reports': section.reports.count(),
            'submitted_reports': section.reports.filter(status='submitted').count(),
            'under_review': section.reports.filter(status='review').count(),
            'approved_reports': section.reports.filter(status='approved').count(),
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


# conference_admin/views.py - добавьте представление

@admin_required
def manage_section_jury(request, section_id):
    """Управление членами жюри секции"""

    section = get_object_or_404(Section, id=section_id)
    jury_members = section.jury_members_list.all().order_by('order')

    # Форма поиска пользователей
    search_form = SearchUserForm(request.GET or None)
    users = []

    if search_form.is_valid() and search_form.cleaned_data.get('search'):
        from users.models import User
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

                # Автоматически заполняем данные из пользователя
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

    # Проверяем, не добавлен ли уже пользователь
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
