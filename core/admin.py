from django.contrib import admin
from django.utils.html import format_html
from .models import ConferenceInfo, ImportantDate, Contact, Organizer, UsefulLink


@admin.register(ConferenceInfo)
class ConferenceInfoAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']

    def has_add_permission(self, request):
        # Разрешаем только одну запись
        return not ConferenceInfo.objects.exists()


@admin.register(ImportantDate)
class ImportantDateAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'order', 'is_active']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'description']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['contact_type', 'title', 'value', 'icon_preview', 'order', 'is_active']
    list_filter = ['contact_type', 'icon_type', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'value']

    fieldsets = (
        ('Основная информация', {
            'fields': ('contact_type', 'title', 'value', 'order', 'is_active')
        }),
        ('Настройка иконки', {
            'fields': (
                'icon_type',
                'icon_bootstrap',
                'icon_image',
                'icon_url',
                'icon_fallback',
            ),
            'description': 'Выберите тип иконки. Для Bootstrap иконок используйте классы типа bi-envelope, bi-telephone. Для изображений можно загрузить файл или указать ссылку.'
        }),
    )

    def icon_preview(self, obj):
        """Превью иконки в списке"""
        icon_data = obj.get_icon_data()

        if icon_data['type'] == 'bootstrap':
            return format_html(
                '<i class="bi {}" style="font-size: 1.5rem; color: #4effff;"></i>',
                icon_data['class']
            )
        elif icon_data['type'] == 'image':
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" />',
                icon_data['url']
            )
        elif icon_data['type'] == 'url':
            fallback = icon_data.get('fallback', '')
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" onerror="this.onerror=null; this.src=\'{}\';" />',
                icon_data['url'],
                fallback if fallback else 'https://via.placeholder.com/30'
            )
        return '-'

    icon_preview.short_description = 'Иконка'


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_preview', 'website', 'order', 'is_active']
    list_filter = ['is_active', 'icon_type']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'description']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'website', 'order', 'is_active')
        }),
        ('Настройка иконки', {
            'fields': (
                'icon_type',
                'icon_bootstrap',
                'icon_image',
                'icon_url',
                'icon_fallback',
            ),
            'description': 'Выберите тип иконки. Для Bootstrap иконок используйте классы типа bi-building, bi-people. Для изображений можно загрузить файл или указать ссылку на логотип.'
        }),
    )

    def icon_preview(self, obj):
        """Превью иконки организатора в списке"""
        icon_data = obj.get_icon_data()

        if icon_data['type'] == 'bootstrap':
            return format_html(
                '<i class="bi {}" style="font-size: 1.5rem; color: #4effff;"></i>',
                icon_data['class']
            )
        elif icon_data['type'] == 'image':
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" />',
                icon_data['url']
            )
        elif icon_data['type'] == 'url':
            fallback = icon_data.get('fallback', '')
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" onerror="this.onerror=null; this.src=\'{}\';" />',
                icon_data['url'],
                fallback if fallback else 'https://via.placeholder.com/30'
            )
        return '-'

    icon_preview.short_description = 'Иконка'


@admin.register(UsefulLink)
class UsefulLinkAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'order', 'is_active']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title']
