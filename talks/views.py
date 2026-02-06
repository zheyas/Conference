from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReportForm
from .models import Report, Section
from authors.models import Author, AuthorReport, AuthorRole
from django.db import models

def index(request):
    """Главная страница"""
    sections = Section.objects.all()
    recent_reports = Report.objects.filter(status='approved').order_by('-created_at')[:6]

    return render(request, 'index.html', {
        'sections': sections,
        'recent_reports': recent_reports,
        'user': request.user
    })


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

            # Проверяем, есть ли у пользователя профиль автора
            try:
                author_profile = request.user.author_profile
            except:
                # Создаем профиль автора для пользователя
                author_profile = Author.objects.create(
                    first_name=request.user.first_name,
                    last_name=request.user.last_name,
                    middle_name=request.user.middle_name or '',
                    email=request.user.email,
                    user=request.user,
                    organization='Оренбургский государственный университет'
                )

            # Добавляем пользователя как основного автора
            main_role, _ = AuthorRole.objects.get_or_create(
                code='main_author',
                defaults={'name': 'Основной автор', 'is_main': True, 'order': 1}
            )

            AuthorReport.objects.create(
                author=author_profile,
                report=report,
                role=main_role,
                is_main_author=True,
                order=0
            )

            messages.success(request, 'Доклад успешно создан! Добавьте других авторов.')
            return redirect('report_edit_authors', report_id=report.id)
    else:
        form = ReportForm()

    return render(request, 'talks/report_create.html', {
        'form': form,
        'sections': Section.objects.all()
    })


@login_required
def report_edit_authors(request, report_id):
    """Редактирование авторов доклада"""
    report = get_object_or_404(Report, id=report_id)

    # Проверяем права доступа
    if report.created_by != request.user:
        messages.error(request, 'У вас нет прав для редактирования этого доклада.')
        return redirect('report_list')

    if request.method == 'POST':
        if 'add_author' in request.POST:
            author_id = request.POST.get('author_id')
            role_id = request.POST.get('role_id')
            is_main = 'is_main' in request.POST
            corresponding = 'corresponding' in request.POST

            try:
                author = Author.objects.get(id=author_id)
                role = AuthorRole.objects.get(id=role_id)

                # Находим максимальный порядок
                max_order = AuthorReport.objects.filter(report=report).aggregate(models.Max('order'))['order__max'] or 0

                # Если устанавливаем основного автора, снимаем флаг с других
                if is_main:
                    AuthorReport.objects.filter(report=report).update(is_main_author=False)

                AuthorReport.objects.create(
                    author=author,
                    report=report,
                    role=role,
                    is_main_author=is_main,
                    corresponding_author=corresponding,
                    order=max_order + 1
                )

                messages.success(request, f'Автор {author.get_full_name()} добавлен.')

            except Author.DoesNotExist:
                messages.error(request, 'Автор не найден.')
            except AuthorRole.DoesNotExist:
                messages.error(request, 'Роль не найдена.')

        elif 'remove_author' in request.POST:
            author_report_id = request.POST.get('author_report_id')
            try:
                author_report = AuthorReport.objects.get(id=author_report_id, report=report)
                author_name = author_report.author.get_full_name()
                author_report.delete()
                messages.success(request, f'Автор {author_name} удален.')
            except AuthorReport.DoesNotExist:
                messages.error(request, 'Связь автор-доклад не найдена.')

        elif 'save_draft' in request.POST:
            report.status = 'draft'
            report.save()
            messages.success(request, 'Доклад сохранен как черновик.')
            return redirect('report_list')

        elif 'submit' in request.POST:
            # Проверяем, что есть хотя бы один автор
            if not AuthorReport.objects.filter(report=report).exists():
                messages.error(request, 'Добавьте хотя бы одного автора.')
            else:
                report.status = 'submitted'
                report.save()
                messages.success(request, 'Доклад успешно отправлен на рассмотрение!')
                return redirect('report_list')

    # Получаем текущих авторов
    current_authors = AuthorReport.objects.filter(report=report).select_related('author', 'role').order_by('order')

    # Получаем всех активных авторов для выбора
    all_authors = Author.objects.filter(is_active=True).order_by('last_name', 'first_name')

    # Получаем все роли
    all_roles = AuthorRole.objects.all().order_by('order')

    return render(request, 'talks/report_edit_authors.html', {
        'report': report,
        'current_authors': current_authors,
        'all_authors': all_authors,
        'all_roles': all_roles,
    })


@login_required
def report_list(request):
    """Список докладов пользователя"""
    # Доклады, созданные пользователем
    created_reports = Report.objects.filter(created_by=request.user).order_by('-created_at')

    # Доклады, где пользователь является автором
    author_reports = Report.objects.filter(
        author_reports__author__user=request.user
    ).distinct().order_by('-created_at')

    # Объединяем, убирая дубликаты
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

    # Проверяем доступ пользователя к докладу
    # Пользователь может видеть доклад если:
    # 1. Он создатель доклада
    # 2. Он является автором доклада
    # 3. Доклад одобрен (публичный доступ)
    has_access = False

    if report.status == 'approved':
        has_access = True
    elif report.created_by == request.user:
        has_access = True
    elif AuthorReport.objects.filter(report=report, author__user=request.user).exists():
        has_access = True

    if not has_access:
        messages.error(request, 'У вас нет доступа к этому докладу.')
        return redirect('report_list')

    # Получаем авторов с их ролями
    authors = AuthorReport.objects.filter(report=report).select_related(
        'author', 'role'
    ).order_by('order')

    return render(request, 'talks/report_detail.html', {
        'report': report,
        'authors': authors
    })


@login_required
def report_edit(request, report_id):
    """Редактирование основного содержания доклада"""
    report = get_object_or_404(Report, id=report_id)

    # Проверяем права доступа
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