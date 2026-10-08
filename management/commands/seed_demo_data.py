"""Заполняет новую базу правдоподобными демонстрационными данными."""

from datetime import date, time, timedelta
from io import BytesIO
import re

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from authors.models import Author, AuthorReport, AuthorRole
from core.models import ConferenceInfo, Contact, ImportantDate, Organizer, UsefulLink
from talks.models import JuryMember, Report, Section
from users.models import User


def make_sample_pdf(title):
    """Создает небольшой валидный PDF-файл для демонстрационного доклада."""
    safe_title = re.sub(r"[^A-Za-z0-9 .,:()-]", "", title)[:70] or "Conference report"
    stream = f"BT /F1 16 Tf 54 740 Td ({safe_title}) Tj /F1 11 Tf 0 -28 Td (IT Spring conference - sample document) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(pdf.tell())
        pdf.write(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_offset = pdf.tell()
    pdf.write(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode())
    return pdf.getvalue()


class Command(BaseCommand):
    help = "Добавить базовые и демонстрационные данные для первого запуска"

    def handle(self, *args, **options):
        if not settings.SEED_DEMO_DATA:
            self.stdout.write("Демо-наполнение отключено (SEED_DEMO_DATA=False).")
            return

        with transaction.atomic():
            self._seed_site_content()
            if Report.objects.exists():
                self.stdout.write("В базе уже есть доклады; демонстрационные записи не добавлялись.")
                return
            self._seed_demo_conference()

        self.stdout.write(self.style.SUCCESS("База заполнена демонстрационными данными конференции."))

    def _seed_site_content(self):
        active_info = ConferenceInfo.objects.filter(is_active=True).first()
        year = active_info.start_date.year if active_info else date.today().year + (date.today().month >= 6)
        title = active_info.title if active_info else f"IT-Весна {year}"
        info, created = ConferenceInfo.objects.get_or_create(
            title=title,
            defaults={
                "subtitle": "Студенческая научно-техническая конференция",
                "description": "Ежегодная конференция Оренбургского государственного университета для молодых исследователей и разработчиков. Доклады, проекты и прикладные исследования в области информационных технологий.",
                "start_date": date(year, 5, 15),
                "end_date": date(year, 5, 17),
                "location": "Оренбургский государственный университет",
                "submission_deadline": date(year, 4, 1),
                "notification_date": date(year, 4, 15),
                "is_active": True,
            },
        )
        if not ConferenceInfo.objects.filter(is_active=True).exists():
            info.is_active = True
            info.save(update_fields=["is_active"])

        contacts = [
            ("email", "Оргкомитет", "conference@osu.ru", "bi-envelope"),
            ("phone", "Телефон оргкомитета", "+7 (3532) 37-24-78", "bi-telephone"),
            ("address", "Адрес", "460018, г. Оренбург, пр. Победы, 13", "bi-geo-alt"),
        ]
        for order, (contact_type, contact_title, value, icon) in enumerate(contacts, 1):
            Contact.objects.get_or_create(
                contact_type=contact_type,
                value=value,
                defaults={"title": contact_title, "icon_bootstrap": icon, "order": order, "is_active": True},
            )

        organizers = [
            ("Факультет математики и информационных технологий ОГУ", "Организатор конференции", "bi-building"),
            ("Студенческое научное общество ОГУ", "Соорганизатор", "bi-people"),
        ]
        for order, (name, description, icon) in enumerate(organizers, 1):
            Organizer.objects.get_or_create(
                name=name,
                defaults={"description": description, "icon_bootstrap": icon, "order": order, "is_active": True},
            )

        links = [
            ("Официальный сайт ОГУ", "https://osu.ru"),
            ("Научная деятельность ОГУ", "https://osu.ru/science"),
        ]
        for order, (link_title, url) in enumerate(links, 1):
            UsefulLink.objects.get_or_create(title=link_title, defaults={"url": url, "order": order})

        dates = [
            ("Начало приема заявок", date(year, 2, 1), "Регистрация участников и подача тезисов"),
            ("Окончание приема заявок", date(year, 4, 1), "Последний день подачи докладов"),
            ("Дни конференции", date(year, 5, 15), "Работа секций и подведение итогов"),
        ]
        for order, (event, event_date, description) in enumerate(dates, 1):
            ImportantDate.objects.get_or_create(
                title=event,
                date=event_date,
                defaults={"description": description, "order": order, "is_active": True},
            )

    def _seed_demo_conference(self):
        active_info = ConferenceInfo.objects.filter(is_active=True).first()
        year = active_info.start_date.year if active_info else date.today().year + (date.today().month >= 6)
        reviewers_data = [
            ("Ирина", "Соколова", "Ивановна", "irina.sokolova@example.test", "Кандидат технических наук", "Доцент"),
            ("Андрей", "Кузнецов", "Петрович", "andrey.kuznetsov@example.test", "Кандидат физико-математических наук", "Доцент"),
            ("Елена", "Морозова", "Сергеевна", "elena.morozova@example.test", "Кандидат экономических наук", ""),
        ]
        reviewers = []
        for first, last, middle, email, degree, title in reviewers_data:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "middle_name": middle,
                    "role": User.Role.REVIEWER,
                    "organization": "Оренбургский государственный университет",
                    "position": "Преподаватель",
                    "academic_degree": degree,
                    "academic_title": title,
                    "is_active": True,
                },
            )
            if user.has_usable_password():
                user.set_unusable_password()
                user.save(update_fields=["password"])
            reviewers.append(user)

        sections_data = [
            ("Искусственный интеллект и анализ данных", "Машинное обучение, компьютерное зрение, обработка естественного языка и интеллектуальные системы."),
            ("Программная инженерия и веб-технологии", "Разработка программных систем, веб-сервисов, мобильных приложений и методы обеспечения качества ПО."),
            ("Информационная безопасность и сети", "Защита информации, криптография, сетевые технологии и анализ угроз."),
        ]
        sections = []
        for index, (name, description) in enumerate(sections_data):
            section, _ = Section.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "date": date(year, 5, 15 + index),
                    "time": time(10 + index, 0),
                    "location": f"Главный корпус ОГУ, аудитория {210 + index}",
                    "jury_chairman": reviewers[index],
                },
            )
            sections.append(section)
            JuryMember.objects.get_or_create(
                section=section,
                user=reviewers[(index + 1) % len(reviewers)],
                defaults={"order": 1},
            )

        role_author, _ = AuthorRole.objects.get_or_create(
            code="author", defaults={"name": "Автор", "description": "Автор доклада", "is_main": True, "order": 1}
        )
        role_supervisor, _ = AuthorRole.objects.get_or_create(
            code="supervisor", defaults={"name": "Научный руководитель", "description": "Научный руководитель работы", "order": 2}
        )

        reports_data = [
            ("Сравнение методов обнаружения объектов на снимках беспилотных летательных аппаратов", "Сопоставлены одноэтапные и двухэтапные модели компьютерного зрения на наборе аэрофотоснимков. Рассмотрены точность локализации, скорость обработки и устойчивость к изменению освещения.", "Нейронные сети, компьютерное зрение, БПЛА", "approved", 0),
            ("Веб-сервис мониторинга качества воздуха на основе открытых данных", "Разработан прототип сервиса, который объединяет данные датчиков и открытых источников, выполняет очистку временных рядов и отображает динамику концентрации загрязняющих веществ.", "веб-разработка, открытые данные, экология", "submitted", 1),
            ("Методы выявления фишинговых страниц с использованием анализа URL", "Исследованы признаки доменных имен и структуры адресов, применяемые для классификации подозрительных ссылок. Проведено сравнение логистической регрессии и градиентного бустинга.", "кибербезопасность, фишинг, классификация", "review", 2),
            ("Оптимизация расписания университетских аудиторий с учетом ограничений", "Предложена модель целочисленной оптимизации для распределения занятий по аудиториям. Учитываются вместимость помещений, доступность оборудования и пожелания учебных групп.", "оптимизация, расписание, исследование операций", "revisions_required", 1),
            ("Применение графовых нейронных сетей для анализа транспортной сети города", "Представление уличной сети в виде графа позволяет оценивать загруженность связанных участков. В работе описан экспериментальный конвейер прогнозирования на исторических данных.", "графовые сети, транспорт, прогнозирование", "resubmitted", 0),
            ("Оценка удобства интерфейса электронного сервиса для студентов", "Проведено небольшое юзабилити-исследование личного кабинета: определены типовые сценарии, собраны наблюдения участников и сформулированы рекомендации по навигации.", "UX, интерфейсы, пользовательское исследование", "rejected", 1),
            ("Защита REST API от повторного воспроизведения запросов", "Рассмотрены угрозы повторной отправки запросов и способы их снижения с помощью временных меток, одноразовых nonce и ограниченного срока действия подписи.", "REST API, безопасность, аутентификация", "draft", 2),
            ("Распознавание печатных формул в студенческих конспектах", "Описан прототип обработки фотографий рукописных конспектов с выделением областей формул и последующим распознаванием печатных математических выражений.", "OCR, обработка изображений, математика", "submitted", 0),
        ]

        student_names = [
            ("Анастасия", "Волкова", "Дмитриевна"), ("Максим", "Егоров", "Алексеевич"),
            ("Дарья", "Федорова", "Ильинична"), ("Кирилл", "Смирнов", "Олегович"),
            ("Полина", "Михайлова", "Андреевна"), ("Илья", "Новиков", "Романович"),
            ("Мария", "Павлова", "Евгеньевна"), ("Денис", "Орлов", "Сергеевич"),
        ]
        for index, (title, abstract, keywords, status, section_index) in enumerate(reports_data):
            first, last, middle = student_names[index]
            email = f"student{index + 1}@example.test"
            author_user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "middle_name": middle,
                    "role": User.Role.USER,
                    "organization": "Оренбургский государственный университет",
                    "is_active": True,
                },
            )
            if author_user.has_usable_password():
                author_user.set_unusable_password()
                author_user.save(update_fields=["password"])
            author, _ = Author.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "middle_name": middle,
                    "user": author_user,
                    "organization": "Оренбургский государственный университет",
                    "department": "Факультет математики и информационных технологий",
                    "position": "Студент",
                },
            )
            report, created = Report.objects.get_or_create(
                title=title,
                defaults={
                    "abstract": abstract,
                    "section": sections[section_index],
                    "created_by": author_user,
                    "status": status,
                    "keywords": keywords,
                    "admin_comment": "Пожалуйста, уточните методику эксперимента и добавьте описание используемого набора данных." if status == "revisions_required" else "",
                    "revision_description": "Добавлены сведения о выборке и критериях оценки." if status == "resubmitted" else "",
                },
            )
            if created:
                report.report_file.save(
                    f"sample-report-{index + 1}.pdf",
                    ContentFile(make_sample_pdf(title)),
                    save=True,
                )
                if status == "resubmitted":
                    Report.objects.filter(pk=report.pk).update(resubmitted_at=timezone.now() - timedelta(days=1))
            AuthorReport.objects.get_or_create(
                author=author,
                report=report,
                defaults={"role": role_author, "order": 0, "is_main_author": True, "corresponding_author": True},
            )
            supervisor = Author.objects.get_or_create(
                email=f"supervisor{index + 1}@example.test",
                defaults={
                    "first_name": reviewers[index % len(reviewers)].first_name,
                    "last_name": reviewers[index % len(reviewers)].last_name,
                    "middle_name": reviewers[index % len(reviewers)].middle_name,
                    "organization": "Оренбургский государственный университет",
                    "department": "Факультет математики и информационных технологий",
                    "academic_degree": reviewers[index % len(reviewers)].academic_degree,
                    "position": "Доцент кафедры",
                },
            )[0]
            AuthorReport.objects.get_or_create(
                author=supervisor,
                report=report,
                defaults={"role": role_supervisor, "order": 1, "contribution": "Научное руководство исследованием"},
            )
