from django.core.management.base import BaseCommand
from talks.models import Report, Review
from django.utils import timezone


class Command(BaseCommand):
    help = 'Обновить статусы докладов на основе рецензий'

    def handle(self, *args, **options):
        reports = Report.objects.all()
        updated_count = 0

        for report in reports:
            old_status = report.status
            reviews = report.reviews.filter(is_visible_to_author=True)

            self.stdout.write(f"\nПроверяем доклад: {report.title}")
            self.stdout.write(f"  Текущий статус: {old_status} ({report.get_status_display()})")
            self.stdout.write(f"  Видимых рецензий: {reviews.count()}")

            if reviews.exists():
                # Выводим информацию о рецензиях
                for review in reviews:
                    self.stdout.write(f"    - Рецензия: {review.reviewer}, статус: {review.status}")

                # Проверяем, есть ли рецензии с доработками
                has_major_revisions = reviews.filter(status='major_revisions').exists()
                has_minor_revisions = reviews.filter(status='minor_revisions').exists()
                has_rejected = reviews.filter(status='rejected').exists()
                has_accepted = reviews.filter(status='accepted').exists()

                self.stdout.write(f"    major_revisions: {has_major_revisions}")
                self.stdout.write(f"    minor_revisions: {has_minor_revisions}")
                self.stdout.write(f"    rejected: {has_rejected}")
                self.stdout.write(f"    accepted: {has_accepted}")

                # Определяем новый статус
                if has_rejected:
                    new_status = 'rejected'
                    reason = "есть отклоненные рецензии"
                elif has_major_revisions:
                    new_status = 'revisions_required'
                    reason = "есть рецензии с значительными доработками"
                    report.needs_revision = True
                elif has_minor_revisions:
                    new_status = 'revisions_required'
                    reason = "есть рецензии с незначительными доработками"
                    report.needs_revision = True
                elif has_accepted and reviews.count() == reviews.filter(status='accepted').count():
                    new_status = 'approved'
                    reason = "все рецензии приняты"
                    report.needs_revision = False
                else:
                    new_status = 'review'
                    reason = "рецензии на рассмотрении"

                # Обновляем, если статус должен измениться
                if new_status != old_status:
                    report.status = new_status
                    if new_status in ['approved', 'rejected', 'revisions_required']:
                        report.reviewed_at = timezone.now()
                    report.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Изменен: {old_status} → {new_status} ({reason})')
                    )
                else:
                    self.stdout.write(f'  ⏸️  Без изменений: {old_status} ({reason})')
            else:
                self.stdout.write(f'  ℹ️  Нет видимых рецензий')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Итого: обновлено {updated_count} докладов из {reports.count()}'))

