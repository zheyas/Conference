# talks/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone


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
            'subject': f'✅ Доклад принят - {settings.SITE_NAME}',
            'template': 'emails/report_approved.html',
            'icon': '✅'
        },
        'rejected': {
            'subject': f'❌ Доклад отклонен - {settings.SITE_NAME}',
            'template': 'emails/report_rejected.html',
            'icon': '❌'
        },
        'revisions_required': {
            'subject': f'✏️ Требуются доработки - {settings.SITE_NAME}',
            'template': 'emails/revision_required.html',
            'icon': '✏️'
        },
        'submitted': {
            'subject': f'📤 Доклад подан - {settings.SITE_NAME}',
            'template': 'emails/report_submitted.html',
            'icon': '📤'
        },
        'review': {
            'subject': f'🔍 Доклад на рассмотрении - {settings.SITE_NAME}',
            'template': 'emails/report_review.html',
            'icon': '🔍'
        },
        'resubmitted': {
            'subject': f'🔄 Доклад отправлен повторно - {settings.SITE_NAME}',
            'template': 'emails/report_resubmitted.html',
            'icon': '🔄'
        },
    }

    # Выбираем шаблон для текущего статуса
    status_info = status_templates.get(report.status, {
        'subject': f'📋 Статус доклада изменен - {settings.SITE_NAME}',
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
        'old_status_display': dict(report.STATUS_CHOICES).get(old_status, old_status) if old_status else None,
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
            print(f"⚠️ У автора {author.get_full_name()} нет email")
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
⚠️ Это автоматическое письмо, созданное системой управления конференцией {settings.SITE_NAME}.
Пожалуйста, не отвечайте на него. Для связи используйте: {settings.DEFAULT_FROM_EMAIL}

© {timezone.now().year} {settings.SITE_NAME} | Оренбургский государственный университет"""

            html_message += f"""
<hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
<p style="color: #666; font-size: 12px; text-align: center;">
    ⚠️ Это автоматическое письмо, созданное системой управления конференцией <strong>{settings.SITE_NAME}</strong>.<br>
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
            print(f" Уведомление отправлено {author.email}")

        except Exception as e:
            failed_sends += 1
            print(f" Ошибка отправки {author.email}: {e}")

    # Логируем результат
    print(f" Отправлено уведомлений: {successful_sends}, ошибок: {failed_sends}")

    return successful_sends, failed_sends
