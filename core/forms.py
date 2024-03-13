from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import MultipleHiddenInput
from .models import User, Book, BookCover, BookReading, BookNote


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
        fields = ("title", "status", "on_hand", "author", "published_year")


class BookStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BookStatusForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = forms.HiddenInput()
        self.fields["author"].widget = MultipleHiddenInput()

    class Meta:
        model = Book
        exclude = ("created_at", "updated_at", "status")


class BookReadingForm(forms.ModelForm):
    class Meta:
        model = BookReading
        fields = ("start_date", "end_date", "finished", "rating")

    rating = forms.IntegerField(min_value=1, max_value=5)
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class CoverForm(forms.ModelForm):
    class Meta:
        model = BookCover
        fields = ("image", "description")


class NoteForm(forms.ModelForm):
    class Meta:
        model = BookNote
        exclude = ("book", "created_at", "updated_at")
