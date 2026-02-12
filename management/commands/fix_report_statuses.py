# management/commands/fix_report_statuses.py
from django.core.management.base import BaseCommand
from talks.models import Report, Review


class Command(BaseCommand):
    help = 'Исправляет статусы докладов на основе рецензий'

    def handle(self, *args, **options):
        reports = Report.objects.all()

        for report in reports:
            old_status = report.status
            report.update_status_based_on_reviews()

            if old_status != report.status:
                self.stdout.write(
                    self.style.SUCCESS(f'Обновлен статус доклада {report.id}: {old_status} -> {report.status}')
                )

        self.stdout.write(self.style.SUCCESS('Статусы успешно обновлены!'))