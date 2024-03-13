from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Book


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("email", "password1", "password2")


class BookForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        self.fields["author"].label = "Author(s)"
        self.fields["published_year"].required = True

    class Meta:
        model = Book
        fields = ("status", "on_hand", "author", "published_year")
