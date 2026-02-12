# talks/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Section, Report, JuryMember
from authors.models import AuthorReport


class AuthorReportInline(admin.TabularInline):
    model = AuthorReport
    extra = 1
    verbose_name = 'Автор'
    verbose_name_plural = 'Авторы'

    fields = ['author', 'role', 'is_main_author', 'corresponding_author', 'order']
    autocomplete_fields = ['author']


class JuryMemberInline(admin.TabularInline):
    model = JuryMember
    extra = 1
    verbose_name = 'Член жюри'
    verbose_name_plural = 'Члены жюри'

    fields = ['user', 'last_name', 'first_name', 'middle_name',
              'organization', 'position', 'academic_degree',
              'academic_title', 'email', 'phone', 'order']

    autocomplete_fields = ['user']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'time', 'location', 'jury_chairman_display', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['name', 'description', 'location']
    ordering = ['date', 'name']

    inlines = [JuryMemberInline]

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'description',
                'icon',
            )
        }),
        ('Дата и место проведения', {
            'fields': (
                'date',
                'time',
                'location',
            )
        }),
        ('Жюри', {
            'fields': (
                'jury_chairman',
            ),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at']

    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.icon.url
            )
        return "Нет иконки"

    icon_preview.short_description = 'Превью иконки'

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.icon:
            readonly_fields.append('icon_preview')
        return readonly_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))

        if obj and obj.icon:
            for i, (title, fieldset_dict) in enumerate(fieldsets):
                if title == 'Основная информация':
                    fieldset_dict['fields'] = ('icon_preview',) + fieldset_dict['fields']
                    break

        return fieldsets

    def jury_chairman_display(self, obj):
        if obj.jury_chairman:
            return obj.jury_chairman.get_full_name()
        return "Не назначен"

    jury_chairman_display.short_description = 'Председатель жюри'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title_short',
        'section',
        'status_badge',
        'authors_count',
        'created_by_display',
        'created_at_short'
    ]

    list_filter = [
        'status',
        'section',
        'created_at'
    ]

    search_fields = [
        'title',
        'abstract',
        'created_by__email',
        'created_by__first_name',
        'created_by__last_name'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'submitted_at',
        'reviewed_at',
        'created_by_display'
    ]

    inlines = [AuthorReportInline]

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'title',
                'abstract',
                'section',
                'keywords',
                'created_by_display'
            )
        }),

        ('Файлы', {
            'fields': (
                'report_file',
                'presentation_file'
            )
        }),

        ('Статус и комментарии', {
            'fields': (
                'status',
                'admin_comment',
                'doi'
            )
        }),

        ('Метаданные', {
            'fields': (
                'created_at',
                'updated_at',
                'submitted_at',
                'reviewed_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def title_short(self, obj):
        if len(obj.title) > 50:
            return f"{obj.title[:50]}..."
        return obj.title

    title_short.short_description = 'Название'
    title_short.admin_order_field = 'title'

    def status_badge(self, obj):
        status_colors = {
            'draft': ('#fef3c7', '#92400e'),
            'submitted': ('#dbeafe', '#1e40af'),
            'review': ('#ffedd5', '#9a3412'),
            'approved': ('#d1fae5', '#065f46'),
            'rejected': ('fee2e2', '#991b1b'),
            'revisions_required': ('#fef3c7', '#92400e'),
        }

        bg_color, text_color = status_colors.get(obj.status, ('#f3f4f6', '#374151'))

        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: 500;">{}</span>',
            bg_color, text_color, obj.get_status_display()
        )

    status_badge.short_description = 'Статус'
    status_badge.admin_order_field = 'status'

    def authors_count(self, obj):
        count = obj.author_reports.count()
        return format_html(
            '<span style="font-weight: bold; color: #4effff;">{}</span>',
            count
        )

    authors_count.short_description = 'Авторы'

    def created_by_display(self, obj):
        if obj.created_by:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                obj.created_by.get_full_name(),
                obj.created_by.email
            )
        return "—"

    created_by_display.short_description = 'Создатель'

    def created_at_short(self, obj):
        return obj.created_at.strftime("%d.%m.%Y")

    created_at_short.short_description = 'Создан'
    created_at_short.admin_order_field = 'created_at'

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(JuryMember)
class JuryMemberAdmin(admin.ModelAdmin):
    list_display = ['section', 'get_full_name', 'organization', 'order']
    list_filter = ['section']
    search_fields = ['last_name', 'first_name', 'middle_name', 'organization', 'user__email']
    ordering = ['section', 'order', 'last_name', 'first_name']

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = 'Имя'
