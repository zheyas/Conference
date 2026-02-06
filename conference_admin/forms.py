from django import forms
from talks.models import Report, Review, Certificate, Section, JuryMember
from authors.models import Author
from users.models import User


class ReportStatusForm(forms.Form):
    """Форма для изменения статуса доклада"""

    status = forms.ChoiceField(
        choices=Report._meta.get_field('status').choices,
        widget=forms.Select(attrs={'class': 'input-field'}),
        label='Новый статус'
    )

    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 4,
            'placeholder': 'Комментарий для авторов'
        }),
        required=False,
        label='Комментарий'
    )


class ReviewForm(forms.ModelForm):
    """Форма для рецензии"""

    class Meta:
        model = Review
        fields = [
            'status', 'comment_for_author', 'comment_for_committee',
            'score_originality', 'score_relevance', 'score_methodology',
            'score_presentation', 'score_quality', 'is_confirmed'
        ]
        widgets = {
            'comment_for_author': forms.Textarea(attrs={
                'class': 'input-field',
                'rows': 6,
                'placeholder': 'Конструктивные замечания и предложения для автора...'
            }),
            'comment_for_committee': forms.Textarea(attrs={
                'class': 'input-field',
                'rows': 4,
                'placeholder': 'Внутренний комментарий для комитета...'
            }),
            'score_originality': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 1,
                'max': 5
            }),
            'score_relevance': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 1,
                'max': 5
            }),
            'score_methodology': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 1,
                'max': 5
            }),
            'score_presentation': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 1,
                'max': 5
            }),
            'score_quality': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 1,
                'max': 5
            }),
        }


class CertificateForm(forms.ModelForm):
    """Форма для создания грамот/сертификатов"""

    class Meta:
        model = Certificate
        fields = [
            'author', 'certificate_type', 'place', 'nomination', 'file'
        ]
        widgets = {
            'author': forms.Select(attrs={'class': 'input-field'}),
            'certificate_type': forms.Select(attrs={'class': 'input-field'}),
            'place': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 1
            }),
            'nomination': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Например: "Лучший научный доклад"'
            }),
            'file': forms.FileInput(attrs={'class': 'input-field'}),
        }


# conference_admin/forms.py

class SectionForm(forms.ModelForm):
    """Форма для управления секциями"""

    class Meta:
        model = Section
        fields = [
            'name', 'description', 'icon', 'date', 'time',
            'location', 'jury_chairman'  # Убрали 'jury_members'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Название секции'
            }),
            'description': forms.Textarea(attrs={
                'class': 'input-field',
                'rows': 5,
                'placeholder': 'Подробное описание секции...'
            }),
            'icon': forms.FileInput(attrs={
                'class': 'input-field',
                'accept': 'image/*'
            }),
            'date': forms.DateInput(attrs={
                'class': 'input-field',
                'type': 'date'
            }),
            'time': forms.TimeInput(attrs={
                'class': 'input-field',
                'type': 'time'
            }),
            'location': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Например: Аудитория 301, Главный корпус'
            }),
            'jury_chairman': forms.Select(attrs={'class': 'input-field'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import User
        # Фильтруем пользователей для выбора председателя жюри
        self.fields['jury_chairman'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')

class UserRoleForm(forms.Form):
    """Форма для изменения роли пользователя"""

    role = forms.ChoiceField(
        choices=[('', '--- Выберите роль ---')] + list(User.Role.choices),
        widget=forms.Select(attrs={'class': 'input-field'}),
        label='Новая роль'
    )


# conference_admin/forms.py - добавьте формы

class JuryMemberForm(forms.ModelForm):
    """Форма для добавления члена жюри"""

    class Meta:
        model = JuryMember
        fields = [
            'user', 'last_name', 'first_name', 'middle_name',
            'organization', 'position', 'academic_degree',
            'academic_title', 'email', 'phone', 'order'
        ]
        widgets = {
            'user': forms.Select(attrs={
                'class': 'input-field',
                'data-type': 'user-select'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Фамилия'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Имя'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Отчество'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Организация'
            }),
            'position': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Должность'
            }),
            'academic_degree': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Ученая степень'
            }),
            'academic_title': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Ученое звание'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-field',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 0,
                'step': 1
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import User
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['user'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.email})"

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        last_name = cleaned_data.get('last_name')
        first_name = cleaned_data.get('first_name')

        # Проверка: либо указан пользователь, либо ФИО
        if user and (last_name or first_name):
            self.add_error(None,
                           'Укажите либо пользователя системы, либо ФИО вручную, но не оба варианта одновременно.')

        if not user and not (last_name and first_name):
            self.add_error(None, 'Если не выбран пользователь системы, необходимо указать фамилию и имя.')

        return cleaned_data


class SearchUserForm(forms.Form):
    """Форма поиска пользователей"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Поиск по ФИО или email...',
            'autocomplete': 'off'
        }),
        label=''
    )
