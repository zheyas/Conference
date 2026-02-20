from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserChangeForm(UserChangeForm):
    """Форма для изменения пользователя с возможностью смены пароля"""

    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


class CustomUserCreationForm(UserCreationForm):
    """Форма для создания пользователя"""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name', 'role')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {
            'fields': (
                'first_name',
                'last_name',
                'middle_name',
                'birth_date',
                'phone',
                'organization',
                'position',
                'academic_degree',
                'academic_title'
            )
        }),
        ('Роли и права доступа', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'role',
                'is_staff',
                'is_active'
            ),
        }),
    )
