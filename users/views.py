from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string

from conference import settings
from .forms import UserRegistrationForm, UserLoginForm

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('index')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.get_full_name()}!')
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль.')
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('index')


@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user': request.user})


def password_reset_request(request):
    """Запрос на восстановление пароля с проверкой ФИО и email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')

        try:
            # Ищем пользователя по email и ФИО
            user = User.objects.get(
                email=email,
                last_name__iexact=last_name,
                first_name__iexact=first_name
            )

            # Генерируем новый пароль
            new_password = get_random_string(length=10)
            user.set_password(new_password)
            user.save()

            # Отправляем новый пароль на почту
            subject = 'Восстановление пароля - IT-Весна'
            message = f"""
            Здравствуйте, {user.get_full_name()}!

            Вы запросили восстановление пароля на сайте конференции IT-Весна.

            Ваш новый пароль: {new_password}

            Рекомендуем сменить этот пароль после входа в личный кабинет.

            С уважением,
            Оргкомитет IT-Весна 
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(request, 'Новый пароль отправлен на ваш email')
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, 'Пользователь с указанными ФИО и email не найден')
        except Exception as e:
            messages.error(request, f'Ошибка при восстановлении пароля: {str(e)}')

    return render(request, 'users/password_reset.html')