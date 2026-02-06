from django.contrib import admin
from django.utils.html import format_html
from .models import Author, AuthorRole, AuthorReport


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Админка для модели Author"""

    list_display = [
        'get_full_name_display',
        'email',
        'organization_short',
        'is_active_badge',
        'created_at_short'
    ]

    list_filter = [
        'is_active',
        'organization',
        'created_at',
        'academic_degree',
        'academic_title'
    ]

    search_fields = [
        'first_name',
        'last_name',
        'middle_name',
        'email',
        'organization',
        'department'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'get_full_name_display'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'get_full_name_display',
                ('first_name', 'last_name', 'middle_name'),
                'email',
                'phone'
            ),
            'classes': ('wide',)
        }),

        ('Академическая информация', {
            'fields': (
                'organization',
                'department',
                'position',
                ('academic_degree', 'academic_title')
            ),
            'classes': ('wide',)
        }),

        ('Идентификаторы', {
            'fields': (
                'orcid',
                'scopus_id',
                'researcher_id'
            ),
            'classes': ('collapse',)
        }),

        ('Системная информация', {
            'fields': (
                'user',
                'is_active'
            ),
            'classes': ('wide',)
        }),

        ('Метаданные', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    # Добавляем действие для массового включения/выключения авторов
    actions = ['activate_authors', 'deactivate_authors']

    # Порядок отображения
    ordering = ['last_name', 'first_name']

    # Пользовательские методы для отображения в списке
    def get_full_name_display(self, obj):
        """Отображение полного имени с иконкой"""
        icon = "👤" if obj.is_active else "👤⚫"
        return format_html(
            '<strong>{}</strong> {}',
            obj.get_full_name(),
            icon
        )

    get_full_name_display.short_description = 'ФИО'
    get_full_name_display.admin_order_field = 'last_name'

    def organization_short(self, obj):
        """Сокращенное название организации"""
        if obj.organization:
            if len(obj.organization) > 30:
                return f"{obj.organization[:30]}..."
            return obj.organization
        return "—"

    organization_short.short_description = 'Организация'

    def is_active_badge(self, obj):
        """Отображение активности в виде бейджа"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 12px; font-size: 12px;">'
                'Активен</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6b7280; color: white; '
                'padding: 3px 8px; border-radius: 12px; font-size: 12px;">'
                'Неактивен</span>'
            )

    is_active_badge.short_description = 'Статус'

    def created_at_short(self, obj):
        """Короткий формат даты создания"""
        return obj.created_at.strftime("%d.%m.%Y")

    created_at_short.short_description = 'Создан'
    created_at_short.admin_order_field = 'created_at'

    # Действия для админки
    def activate_authors(self, request, queryset):
        """Активировать выбранных авторов"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Активировано {updated} авторов."
        )

    activate_authors.short_description = "Активировать выбранных авторов"

    def deactivate_authors(self, request, queryset):
        """Деактивировать выбранных авторов"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Деактивировано {updated} авторов."
        )

    deactivate_authors.short_description = "Деактивировать выбранных авторов"

    # Настройка формы для добавления
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Помечаем обязательные поля
        form.base_fields['first_name'].required = True
        form.base_fields['last_name'].required = True
        form.base_fields['email'].required = True

        return form


@admin.register(AuthorRole)
class AuthorRoleAdmin(admin.ModelAdmin):
    """Админка для ролей авторов"""

    list_display = [
        'name',
        'code',
        'is_main_badge',
        'order',
        'author_count'
    ]

    list_filter = [
        'is_main'
    ]

    search_fields = [
        'name',
        'code',
        'description'
    ]

    ordering = ['order', 'name']

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'code',
                'description'
            )
        }),

        ('Настройки', {
            'fields': (
                'is_main',
                'order'
            )
        }),
    )

    # Пользовательские методы для отображения
    def is_main_badge(self, obj):
        """Отображение флага основной роли"""
        if obj.is_main:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; '
                'padding: 3px 8px; border-radius: 12px; font-size: 12px;">'
                'Основная</span>'
            )
        return "—"

    is_main_badge.short_description = 'Основная роль'

    def author_count(self, obj):
        """Количество авторов с этой ролью"""
        count = obj.author_reports.count()
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )

    author_count.short_description = 'Кол-во связей'


@admin.register(AuthorReport)
class AuthorReportAdmin(admin.ModelAdmin):
    """Админка для связи автор-доклад"""

    list_display = [
        'author_info',
        'report_info',
        'role_display',
        'is_main_badge',
        'corresponding_badge',
        'order_display',
        'created_at_short'
    ]

    list_filter = [
        'role',
        'is_main_author',
        'corresponding_author',
        'created_at'
    ]

    search_fields = [
        'author__first_name',
        'author__last_name',
        'author__email',
        'report__title'
    ]

    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'author',
                'report',
                'role'
            )
        }),

        ('Настройки', {
            'fields': (
                'order',
                'is_main_author',
                'corresponding_author',
                'contribution'
            )
        }),

        ('Метаданные', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    # Автозаполнение полей
    autocomplete_fields = ['author', 'report']

    # Пользовательские методы для отображения
    def author_info(self, obj):
        """Информация об авторе"""
        if obj.author:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                obj.author.get_full_name(),
                obj.author.email
            )
        return "—"

    author_info.short_description = 'Автор'
    author_info.admin_order_field = 'author__last_name'

    def report_info(self, obj):
        """Информация о докладе"""
        if obj.report:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                obj.report.title[:50] + "..." if len(obj.report.title) > 50 else obj.report.title,
                obj.report.get_status_display() if hasattr(obj.report, 'get_status_display') else ""
            )
        return "—"

    report_info.short_description = 'Доклад'
    report_info.admin_order_field = 'report__title'

    def role_display(self, obj):
        """Отображение роли"""
        if obj.role:
            return format_html(
                '<span style="color: #4effff; font-weight: bold;">{}</span>',
                obj.role.name
            )
        return "—"

    role_display.short_description = 'Роль'

    def is_main_badge(self, obj):
        """Бейдж основного автора"""
        if obj.is_main_author:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 12px; font-size: 12px;">'
                'Основной</span>'
            )
        return "—"

    is_main_badge.short_description = 'Основной'

    def corresponding_badge(self, obj):
        """Бейдж автора для корреспонденции"""
        if obj.corresponding_author:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; '
                'padding: 3px 8px; border-radius: 12px; font-size: 12px;">'
                'Для корреспонденции</span>'
            )
        return "—"

    corresponding_badge.short_description = 'Корреспонденция'

    def order_display(self, obj):
        """Отображение порядка"""
        return format_html(
            '<span style="font-weight: bold; font-size: 16px;">{}</span>',
            obj.order
        )

    order_display.short_description = 'Порядок'

    def created_at_short(self, obj):
        """Короткая дата создания"""
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    created_at_short.short_description = 'Создано'
    created_at_short.admin_order_field = 'created_at'


# Опционально: Inline для отображения связей автор-доклад в админке автора
class AuthorReportInline(admin.TabularInline):
    """Inline для отображения докладов автора"""
    model = AuthorReport
    extra = 0
    can_delete = True
    show_change_link = True

    fields = [
        'report',
        'role',
        'is_main_author',
        'corresponding_author',
        'order'
    ]

    readonly_fields = []
    autocomplete_fields = ['report']

    # Ограничиваем количество отображаемых записей
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('report', 'role')

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True


# Опционально: Inline для отображения авторов в админке доклада
class AuthorReportInlineForReport(admin.TabularInline):
    """Inline для отображения авторов доклада"""
    model = AuthorReport
    extra = 1
    can_delete = True

    fields = [
        'author',
        'role',
        'is_main_author',
        'corresponding_author',
        'order',
        'contribution'
    ]

    autocomplete_fields = ['author']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author', 'role')
