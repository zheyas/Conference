from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'example@osu.ru'
        }),
        label='Электронная почта'
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Иван'
        }),
        label='Имя'
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Иванов'
        }),
        label='Фамилия'
    )

    middle_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Иванович'
        }),
        label='Отчество'
    )

    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'input-field',
            'type': 'date'
        }),
        label='Дата рождения'
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Пароль'
        }),
        label='Пароль'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Подтверждение пароля'
        }),
        label='Подтверждение пароля'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'middle_name', 'birth_date', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'example@osu.ru'
        }),
        label='Электронная почта'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Пароль'
        }),
        label='Пароль'
    )
