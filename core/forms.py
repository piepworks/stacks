from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Book


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("email", "password1", "password2")


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ("status", "on_hand")
