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
from django.utils.text import slugify
from django.urls import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFit
from core.image_helpers import rename_image


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
    # Add more fields here.

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Author(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("author_detail", args=(self.slug,))


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
    slug = models.SlugField(unique=True)
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
    genre = models.ForeignKey(
        BookGenre,
        on_delete=models.SET_NULL,
        related_name="books",
        null=True,
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
        blank=True,
    )
    archived = models.BooleanField(default=False)
    olid = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Create a slug based on the title field if none is provided
        if not self.slug:
            self.slug = slugify(self.title)

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

    def get_absolute_url(self):
        return reverse("book_detail", args=(self.slug,))

    @property
    def status_display(self):
        return self.get_status_display()

    @property
    def latest_reading(self):
        return BookReading.objects.filter(book=self).order_by("-start_date").first()


class BookCover(models.Model):
    image = ProcessedImageField(
        upload_to=rename_image,
        processors=[ResizeToFit(width=600, upscale=False)],
        format="JPEG",
        options={"quality": 70},
    )
    thumbnail = ImageSpecField(
        source="image",
        processors=[ResizeToFit(width=300, upscale=False)],
        format="JPEG",
        options={"quality": 60},
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="covers")
    description = models.CharField(
        max_length=100,
        blank=True,
        help_text="E.g. “First edition,” etc.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cover of {self.book}"

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

                self.image.save(os.path.basename(url), File(img_tmp), save=True)
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
            return (self.end_date - self.start_date).days
        return None


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
