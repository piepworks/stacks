import os
import requests
import datetime
import pillow_avif  # noqa: F401 (ignore "unused import" error)
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import date
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.urls import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
from core.image_helpers import rename_image, resize_image
from ordered_model.models import OrderedModel


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_("email address"), unique=True)
    timezone = models.CharField(
        max_length=40,
        blank=True,
        choices=settings.TIME_ZONES,
        default=settings.TIME_ZONE,
    )

    # Add more fields here.

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Changelog(models.Model):
    date = models.DateField(default=datetime.date.today)
    summary = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Changelog Entry"
        verbose_name_plural = "Changelog Entries"

    def __str__(self):
        return f"Changes for {self.date}"


class Author(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="authors")
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("user", "name"),)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("author_detail", args=(self.pk,))

    @property
    def book_count(self):
        return (
            Book.objects.filter(
                author=self,
                user=self.user,
            )
            .exclude(archived=True)
            .count()
        )


class BookFormat(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BookType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name


class BookGenre(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["parent__name", "name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name


class BookLocation(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="books")
    author = models.ManyToManyField(Author)
    published_year = models.IntegerField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("wishlist", "Wishlist"),
            ("backlog", "Backlog"),
            ("to-read", "To Read"),
            ("reading", "Reading"),
            ("finished", "Finished"),
            ("dnf", "Did Not Finish"),
        ],
    )
    type = models.ForeignKey(
        BookType,
        on_delete=models.SET_NULL,
        related_name="books",
        null=True,
        blank=True,
    )
    genre = models.ManyToManyField(
        BookGenre,
        related_name="books",
        help_text="Choose as many as you like",
        blank=True,
    )
    format = models.ManyToManyField(
        BookFormat,
        related_name="books",
        help_text="Choose as many as you have",
        blank=True,
    )
    location = models.ManyToManyField(
        BookLocation,
        related_name="books",
        help_text="For digital or audio books, choose the device or platform",
        blank=True,
    )
    archived = models.BooleanField(default=False)
    olid = models.CharField(max_length=100, blank=True, verbose_name="Open Library ID")
    imported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("user", "title"),)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        new = not self.pk

        if self.pk:
            old_status = Book.objects.get(pk=self.pk).status
            new_status = self.status

            if old_status != new_status:
                # Add a BookReading with the current date as a start date
                if new_status == "reading":
                    BookReading.objects.create(
                        book=self, start_date=datetime.date.today()
                    )

                # Add the current date as an `end_date` to the most recent BookReading (if any) and mark it `finished`
                elif new_status == "finished":
                    reading = (
                        BookReading.objects.filter(book=self, end_date=None)
                        .order_by("-start_date")
                        .first()
                    )
                    if reading:
                        reading.end_date = datetime.date.today()
                        reading.finished = True
                        reading.save()

                # Add an `end_date` to the latest BookReading (if any) but don't mark it `finished`
                elif new_status == "dnf":
                    reading = (
                        BookReading.objects.filter(book=self, end_date=None)
                        .order_by("-start_date")
                        .first()
                    )
                    if reading:
                        reading.end_date = datetime.date.today()
                        reading.save()

        super().save(*args, **kwargs)

        if new and self.status == "reading":
            BookReading.objects.create(book=self, start_date=datetime.date.today())

    def get_absolute_url(self):
        return reverse("book_detail", args=(self.pk,))

    @property
    def status_display(self):
        return self.get_status_display()

    # Maybe use an annotation for this instead of a @property
    # https://stackoverflow.com/questions/2143438/is-it-possible-to-reference-a-property-using-djangos-queryset-values-list#comment131258575_2143575
    @property
    def original_status(self):
        # Check BookStatusChange
        # If it does have status changes, return the first one
        # If it doesn't have any, return current status
        first_change = self.status_changes.all().order_by("changed_at").first()

        if first_change:
            return first_change.old_status
        else:
            return self.status

    @property
    def latest_reading(self):
        return BookReading.objects.filter(book=self).order_by("-start_date").first()


class BookCover(OrderedModel):
    image = models.ImageField(
        upload_to=rename_image,
        height_field="image_height",
        width_field="image_width",
        blank=True,
        null=True,
    )
    image_width = models.PositiveSmallIntegerField(blank=True, null=True)
    image_height = models.PositiveSmallIntegerField(blank=True, null=True)
    thumbnail = models.ImageField(
        upload_to=rename_image,
        blank=True,
        null=True,
        height_field="thumbnail_height",
        width_field="thumbnail_width",
    )
    thumbnail_width = models.PositiveSmallIntegerField(blank=True, null=True)
    thumbnail_height = models.PositiveSmallIntegerField(blank=True, null=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="covers")
    order_with_respect_to = "book"
    description = models.CharField(
        max_length=100,
        blank=True,
        help_text="E.g. “First edition,” etc.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cover of {self.book}"

    def save(self, *args, **kwargs):
        if not self.pk and self.image:
            self.image = resize_image(self.image, width=600)
            self.thumbnail = resize_image(self.image, width=300)
        elif not self.thumbnail and self.image:
            self.thumbnail = resize_image(self.image, width=300)

        super().save(*args, **kwargs)

    def save_cover_from_url(self, url):
        if url != "":
            try:
                r = requests.get(url, headers={"User-Agent": "Stacks"})
            except requests.exceptions.RequestException:
                return False

            if r.status_code == 200:
                img_tmp = NamedTemporaryFile(delete=True)
                img_tmp.write(r.content)
                img_tmp.flush()

                self.image.save(os.path.basename(url)[:100], File(img_tmp), save=True)
                return True
            else:
                return False
        else:
            return False


class BookReading(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="readings")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    finished = models.BooleanField(default=False)
    rating = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["book", "start_date"]
        ordering = ["-start_date"]

    def __str__(self):
        return f"Reading of {self.book} / Starting on {self.start_date}"

    @property
    def duration(self):
        if self.end_date:
            # The minium duration is 1 day
            return (self.end_date - self.start_date).days + 1
        return None


class Series(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="series")
    books = models.ManyToManyField(
        Book, through="SeriesBook", related_name="series", blank=True
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "title"]
        verbose_name_plural = "Series"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("series_detail", args=(self.pk,))


class SeriesBook(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(null=True, blank=True)
    order_label = models.CharField(
        max_length=10,
        blank=True,
        help_text="If you want something other than its position in the series. E.g. “4.5”",
    )

    class Meta:
        unique_together = ["series", "book"]
        ordering = ["order"]

    def __str__(self):
        return f"{self.series}: {self.order}. {self.book}"

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = self.series.books.count() + 1

        super().save(*args, **kwargs)


class BookNote(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="notes")
    text = models.TextField()
    page = models.PositiveSmallIntegerField(null=True, blank=True)
    percentage = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note for {self.book} / Created {date(self.created_at, 'Y-m-d')}"


class BookStatusChange(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="status_changes",
    )
    old_status = models.CharField(max_length=200)
    new_status = models.CharField(max_length=200)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{date(self.changed_at, 'Y-m-d')} / {self.book} Changed from “{self.old_status}” to “{self.new_status}”"


@receiver(pre_save, sender=Book)
def track_status_changes(sender, instance, **kwargs):
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            BookStatusChange.objects.create(
                book=old_instance,
                old_status=old_instance.status,
                new_status=instance.status,
            )
    except sender.DoesNotExist:
        pass
