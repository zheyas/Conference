# management/commands/update_report_status.py
from django.core.management.base import BaseCommand
from talks.models import Report, Review


class Command(BaseCommand):
    help = 'Обновить статусы докладов на основе рецензий'

    def handle(self, *args, **options):
        reports = Report.objects.filter(status__in=['review', 'submitted'])

        for report in reports:
            reviews = report.reviews.filter(is_visible_to_author=True)

            if reviews.exists():
                # Проверяем, есть ли рецензии с доработками
                has_revisions_required = reviews.filter(
                    status__in=['major_revisions', 'minor_revisions']
                ).exists()

                if has_revisions_required and report.status != 'revisions_required':
                    report.status = 'revisions_required'
                    report.needs_revision = True
                    report.reviewed_at = reviews.latest('created_at').created_at
                    report.save()
                    self.stdout.write(f'Обновлен статус доклада {report.id}: {report.title}')

        self.stdout.write(self.style.SUCCESS('Статусы обновлены!'))
