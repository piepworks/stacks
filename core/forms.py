from django import forms
from django.forms.widgets import MultipleHiddenInput
from django.forms import modelformset_factory
from django_registration.forms import RegistrationForm
from .models import (
    User,
    Book,
    BookCover,
    BookReading,
    BookNote,
    Author,
    Series,
    SeriesBook,
)
from .fields import GroupedModelChoiceField


class RegisterForm(RegistrationForm):
    email = forms.EmailField()
    usable_password = None

    class Meta(RegistrationForm.Meta):
        model = User
        fields = ("email", "password1", "password2")


class ImportBooksForm(forms.Form):
    csv = forms.FileField(label="Then, upload the CSV file here")


class OpenLibrarySearchForm(forms.Form):
    everything = forms.CharField(label="All fields", required=False)
    title = forms.CharField(label="Title", required=False)
    author = forms.CharField(label="Author", required=False)

    def __init__(self, *args, autofocus=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.autofocus = autofocus
        self.attrs = {"autofocus": True} if self.autofocus else {}
        self.fields["title"].widget.attrs.update(self.attrs)


class BookForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(BookForm, self).__init__(*args, **kwargs)
        self.fields["author"].label = "Author(s)"
        self.fields["author"].queryset = Author.objects.filter(user=self.user)
        self.fields["location"].label = "Location(s)"
        self.fields["genre"].label = "Genre(s)"
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
            "olid",
            "pages",
        )


class BookStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BookStatusForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = forms.HiddenInput()
        self.fields["author"].widget = MultipleHiddenInput()
        self.fields["format"].widget = MultipleHiddenInput()
        self.fields["location"].widget = MultipleHiddenInput()
        self.fields["genre"].widget = MultipleHiddenInput()

    class Meta:
        model = Book
        exclude = ("created_at", "updated_at", "status")


class BookReadingForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )
    rating = forms.IntegerField(
        min_value=1, max_value=5, required=False, help_text="1-5 stars"
    )

    class Meta:
        model = BookReading
        fields = ("finished", "start_date", "end_date", "rating", "review")


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
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

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


class SeriesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SeriesForm, self).__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"autofocus": True})

    class Meta:
        model = Series
        fields = (
            "title",
            "description",
        )


class SeriesBookForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SeriesBookForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != "order":
                self.fields[field].widget = forms.HiddenInput()

    class Meta:
        model = SeriesBook
        exclude = [
            "order_label",
        ]


SeriesBookFormSet = modelformset_factory(
    SeriesBook,
    form=SeriesBookForm,
    extra=0,
)


class SettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "email",
            "timezone",
        )
