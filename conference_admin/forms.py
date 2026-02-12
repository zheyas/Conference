# conference_admin/forms.py
from django import forms
from django.core.exceptions import ValidationError
from talks.models import Report, Section, Certificate, JuryMember
from authors.models import Author
from users.models import User
import os


# 1. Форма для изменения статуса доклада с комментариями
class ReportStatusForm(forms.ModelForm):
    """Форма для изменения статуса доклада с комментариями"""

    class Meta:
        model = Report
        fields = ['status', 'admin_comment']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Ваши замечания и предложения для авторов...',
                'class': 'w-full px-3 py-2 border rounded-lg'
            }),
        }
        labels = {
            'status': 'Новый статус',
            'admin_comment': 'Комментарий для авторов'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Упрощенные статусы для администратора
        self.fields['status'].choices = [
            ('submitted', 'Подано'),
            ('review', 'На рассмотрении'),
            ('approved', 'Одобрено'),
            ('rejected', 'Отклонено'),
            ('revisions_required', 'Требуются доработки'),
        ]


# 2. Форма для грамот/сертификатов
class CertificateForm(forms.ModelForm):
    """Форма для создания грамот и сертификатов"""

    class Meta:
        model = Certificate
        fields = ['author', 'certificate_type', 'place', 'nomination', 'file', 'is_published']
        widgets = {
            'author': forms.Select(attrs={'class': 'form-select'}),
            'certificate_type': forms.Select(attrs={'class': 'form-select'}),
            'place': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
            'nomination': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Лучшая презентация и т.д.'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('Файл слишком большой. Максимальный размер: 5MB')

            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise ValidationError('Неподдерживаемый формат файла. Используйте PDF, JPG, JPEG или PNG.')

        return file


# 3. Форма для секций
class SectionForm(forms.ModelForm):
    """Форма для создания и редактирования секций"""

    class Meta:
        model = Section
        fields = ['name', 'description', 'icon', 'date', 'time', 'location', 'jury_chairman']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название секции'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Описание секции'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-input',
                'type': 'time'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Аудитория, зал, онлайн'
            }),
            'jury_chairman': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_icon(self):
        icon = self.cleaned_data.get('icon')
        if icon:
            if icon.size > 2 * 1024 * 1024:
                raise ValidationError('Файл иконки слишком большой. Максимальный размер: 2MB')

            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg']
            if not any(icon.name.lower().endswith(ext) for ext in allowed_extensions):
                raise ValidationError('Неподдерживаемый формат изображения. Используйте JPG, PNG, GIF или SVG.')

        return icon


# 4. Форма для изменения роли пользователя
class UserRoleForm(forms.Form):
    """Форма для изменения роли пользователя"""

    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Новая роль',
        required=True
    )


# 5. Форма для поиска пользователей
class SearchUserForm(forms.Form):
    """Форма для поиска пользователей"""

    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Поиск по ФИО или email...'
        }),
        label='Поиск пользователей',
        required=False,
        max_length=100
    )


# 6. Форма для членов жюри
class JuryMemberForm(forms.ModelForm):
    """Форма для добавления членов жюри"""

    class Meta:
        model = JuryMember
        fields = ['user', 'last_name', 'first_name', 'middle_name', 'organization',
                  'position', 'academic_degree', 'academic_title', 'email', 'phone', 'order']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-input'}),
            'organization': forms.TextInput(attrs={'class': 'form-input'}),
            'position': forms.TextInput(attrs={'class': 'form-input'}),
            'academic_degree': forms.TextInput(attrs={'class': 'form-input'}),
            'academic_title': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'type': 'email'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'type': 'tel'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')

        if user:
            if not cleaned_data.get('last_name'):
                cleaned_data['last_name'] = user.last_name
            if not cleaned_data.get('first_name'):
                cleaned_data['first_name'] = user.first_name
            if not cleaned_data.get('middle_name'):
                cleaned_data['middle_name'] = user.middle_name
            if not cleaned_data.get('email'):
                cleaned_data['email'] = user.email
            if not cleaned_data.get('organization'):
                cleaned_data['organization'] = user.organization or ''
            if not cleaned_data.get('position'):
                cleaned_data['position'] = user.position or ''

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            section = self.instance.section if self.instance.pk else None
            if section and JuryMember.objects.filter(
                    section=section,
                    email=email
            ).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
                raise ValidationError('Член жюри с таким email уже существует в этой секции.')

        return email
