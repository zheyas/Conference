from .models import ConferenceInfo, Contact, Organizer, UsefulLink


def core_context(request):
    """Добавляет данные core во все шаблоны"""

    # Получаем активную конференцию
    conference = ConferenceInfo.objects.filter(is_active=True).first()

    return {
        'conference_info': conference,
        'contacts': Contact.objects.filter(is_active=True).order_by('order'),
        'organizers': Organizer.objects.filter(is_active=True).order_by('order'),
        'useful_links': UsefulLink.objects.filter(is_active=True).order_by('order'),
    }
