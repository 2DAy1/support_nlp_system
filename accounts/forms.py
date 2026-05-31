from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'Імʼя користувача',
            'email': 'Email',
            'password1': 'Пароль',
            'password2': 'Підтвердження пароля',
        }