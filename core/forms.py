from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserBook


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("email", "password1", "password2")


class UserBookForm(forms.ModelForm):
    class Meta:
        model = UserBook
        fields = ("book", "status", "on_hand")
