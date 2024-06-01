from django import forms
from django.forms.widgets import MultipleHiddenInput
from django_registration.forms import RegistrationForm
from .models import User, Book, BookCover, BookReading, BookNote, Author
from .fields import GroupedModelChoiceField


class RegisterForm(RegistrationForm):
    email = forms.EmailField()

    class Meta(RegistrationForm.Meta):
        model = User
        fields = ("email", "password1", "password2")


class BookForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(BookForm, self).__init__(*args, **kwargs)
        self.fields["author"].label = "Author(s)"
        self.fields["author"].queryset = Author.objects.filter(user=self.user)
        self.fields["location"].label = "Location(s)"
        self.fields["genre"] = GroupedModelChoiceField(
            queryset=self.fields["genre"].queryset.order_by("parent", "name"),
            choices_groupby="parent",
            required=False,
        )
        self.fields["type"] = GroupedModelChoiceField(
            queryset=self.fields["type"].queryset.order_by("parent", "name"),
            choices_groupby="parent",
            required=False,
        )

    class Meta:
        model = Book
        fields = (
            "title",
            "status",
            "author",
            "type",
            "genre",
            "published_year",
            "format",
            "location",
        )


class BookStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BookStatusForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = forms.HiddenInput()
        self.fields["author"].widget = MultipleHiddenInput()
        self.fields["format"].widget = MultipleHiddenInput()
        self.fields["location"].widget = MultipleHiddenInput()

    class Meta:
        model = Book
        exclude = ("created_at", "updated_at", "status")


class BookReadingForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )
    rating = forms.IntegerField(min_value=1, max_value=5, required=False)

    class Meta:
        model = BookReading
        fields = ("start_date", "end_date", "finished", "rating")


class BookCoverForm(forms.ModelForm):
    url = forms.URLField(
        required=False, label="URL", help_text="If you don't have a file"
    )
    image = forms.ImageField(required=False)  # make image field optional

    class Meta:
        model = BookCover
        fields = ("image", "url", "description")

    def __init__(self, *args, **kwargs):
        self.book = kwargs.pop("book", None)
        super(BookCoverForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get("image")
        url = cleaned_data.get("url")

        if not image and url:
            self.instance.book = self.book
            success = self.instance.save_cover_from_url(url)

            if not success:
                self.add_error("url", "Failed to save cover from URL")

        return cleaned_data


class BookNoteForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 3, "x-model": "note"}))

    class Meta:
        model = BookNote
        exclude = ("book", "page", "percentage", "created_at", "updated_at")


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = (
            "name",
            "bio",
        )


class SettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "email",
            "timezone",
        )
