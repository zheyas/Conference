from django.shortcuts import render
from core.models import Contact, Organizer, UsefulLink


def contacts_view(request):
    """Страница контактов"""

    contacts = Contact.objects.filter(is_active=True).order_by('order')
    organizers = Organizer.objects.filter(is_active=True).order_by('order')
    useful_links = UsefulLink.objects.filter(is_active=True).order_by('order')

    # Группируем контакты по типу для удобства
    contacts_by_type = {}
    for contact in contacts:
        if contact.contact_type not in contacts_by_type:
            contacts_by_type[contact.contact_type] = []
        contacts_by_type[contact.contact_type].append(contact)

    return render(request, 'conference/contacts.html', {
        'contacts': contacts,
        'contacts_by_type': contacts_by_type,
        'organizers': organizers,
        'useful_links': useful_links,
    })
