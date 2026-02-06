from django.apps import AppConfig


class ConferenceAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'conference_admin'
    verbose_name = 'Администрирование конференции'