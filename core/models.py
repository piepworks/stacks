import os
import requests
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import date
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from core.image_helpers import rename_image, resize_and_optimize_image


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
    on_hand = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # Create a slug based on the title field if none is provided
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.title.replace(" ", "-").lower()
        super().save(*args, **kwargs)

    @property
    def status_display(self):
        return self.get_status_display()


class BookCover(models.Model):
    image = models.ImageField(upload_to=rename_image, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="covers")
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
        super().save(*args, **kwargs)
        if self.image and self.image.width > 600:
            self.image = resize_and_optimize_image(self, self.image.name)

    def save_cover_from_url(self, url):
        if url != "":
            r = requests.get(url)

            if r.status_code == 200:
                img_tmp = NamedTemporaryFile(delete=True)
                img_tmp.write(r.content)
                img_tmp.flush()

                self.image.save(os.path.basename(url), File(img_tmp), save=True)
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
    format = models.CharField(
        max_length=20,
        choices=[
            ("physical", "Physical"),
            ("digital", "Digital"),
            ("audio", "Audio"),
        ],
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["book", "start_date"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reading of {self.book} / Starting on {self.start_date}"


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
