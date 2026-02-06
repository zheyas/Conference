from django import forms
from django.core.exceptions import ValidationError
from .models import Author, AuthorRole
from users.models import User


class AuthorForm(forms.ModelForm):
    """Форма для создания/редактирования автора"""

    class Meta:
        model = Author
        fields = [
            'first_name', 'last_name', 'middle_name', 'email',
            'organization', 'department', 'academic_degree', 'academic_title',
            'position', 'phone', 'orcid', 'scopus_id', 'researcher_id'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Иван'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Иванов'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Иванович'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-field',
                'placeholder': 'ivanov@example.com'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Оренбургский государственный университет'
            }),
            'department': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Факультет математики и информационных технологий'
            }),
            'academic_degree': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'канд. техн. наук'
            }),
            'academic_title': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'доцент'
            }),
            'position': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'старший преподаватель'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '+7 (3532) 37-24-78'
            }),
            'orcid': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '0000-0000-0000-0000'
            }),
            'scopus_id': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '12345678900'
            }),
            'researcher_id': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'A-1234-5678'
            }),
        }
        labels = {
            'first_name': 'Имя *',
            'last_name': 'Фамилия *',
            'middle_name': 'Отчество',
            'email': 'Электронная почта *',
            'organization': 'Организация',
            'department': 'Кафедра/факультет',
            'academic_degree': 'Ученая степень',
            'academic_title': 'Ученое звание',
            'position': 'Должность',
            'phone': 'Телефон',
            'orcid': 'ORCID ID',
            'scopus_id': 'Scopus Author ID',
            'researcher_id': 'ResearcherID',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Author.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Автор с таким email уже существует')
        return email

    def clean_user(self):
        """Валидация связи с пользователем"""
        user = self.cleaned_data.get('user')
        if user and Author.objects.filter(user=user).exclude(pk=self.instance.pk).exists():
            raise ValidationError('У этого пользователя уже есть профиль автора')
        return user


class AuthorSearchForm(forms.Form):
    """Форма для поиска авторов"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Поиск по ФИО, email, организации...'
        }),
        label='Поиск'
    )

    organization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Фильтр по организации...'
        }),
        label='Организация'
    )


class AddAuthorToReportForm(forms.Form):
    """Форма для добавления автора к докладу"""

    author = forms.ModelChoiceField(
        queryset=Author.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'input-field'
        }),
        label='Автор'
    )

    role = forms.ModelChoiceField(
        queryset=AuthorRole.objects.all(),
        widget=forms.Select(attrs={
            'class': 'input-field'
        }),
        label='Роль'
    )

    is_main_author = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox-field'
        }),
        label='Основной автор'
    )

    corresponding_author = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox-field'
        }),
        label='Автор для корреспонденции'
    )

    contribution = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 3,
            'placeholder': 'Опишите вклад автора в работу...'
        }),
        label='Вклад в работу'
    )
