from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group
from django.db.models import Count
from .models import (
    User,
    Book,
    Author,
    BookCover,
    BookReading,
    BookNote,
    BookType,
    BookGenre,
    BookFormat,
    BookLocation,
    Changelog,
    Series,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "timezone")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "book_count", "series_count", "is_active", "last_login")
    list_filter = ("is_active",)
    search_fields = ("email",)
    ordering = ("-last_login",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _book_count=Count("books", distinct=True),
            _series_count=Count("series", distinct=True),
        )
        return qs

    def book_count(self, obj):
        return obj._book_count

    def series_count(self, obj):
        return obj._series_count

    book_count.admin_order_field = "_book_count"
    book_count.admin_order_field = "_series_count"
    book_count.short_description = "Books"


class BookCoverInline(admin.TabularInline):
    model = BookCover
    extra = 1


class BookAuthorInline(admin.TabularInline):
    verbose_name = "Author"
    model = Book.author.through
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "authors_list", "formats_list", "imported")
    list_filter = ("user", "archived", "status")
    inlines = [BookAuthorInline, BookCoverInline]
    exclude = ("author",)
    actions = ["archive_books", "unarchive_books"]

    def archive_books(self, request, queryset):
        queryset.update(archived=True)

    def unarchive_books(self, request, queryset):
        queryset.update(archived=False)

    def authors_list(self, obj):
        return ", ".join([author.name for author in obj.author.all()])

    def formats_list(self, obj):
        return ", ".join([format.name for format in obj.format.all()])

    unarchive_books.short_description = "Un-archive selected books"
    archive_books.short_description = "Archive selected books"
    authors_list.short_description = "Authors"


@admin.register(BookCover)
class BookCoverAdmin(admin.ModelAdmin):
    list_display = ("book", "image_tag", "updated_at")
    readonly_fields = ("image_tag",)

    def image_tag(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" width="150" />')
        return "-"

    image_tag.short_description = "Cover"


@admin.register(BookType)
class BookTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug", "parent")


@admin.register(BookGenre)
class BookGenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("__str__", "slug")


@admin.register(BookFormat)
class BookFormatAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug")


@admin.register(BookLocation)
class BookLocationAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug")


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "book_count")

    list_filter = ("user",)

    def book_count(self, obj):
        return obj.book_set.count()

    book_count.short_description = "Book Count"

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ("display_books",)

    def display_books(self, obj):
        links = "".join(
            f'<p><a href="{reverse("admin:core_book_change", args=[book.pk])}">{book}</a></p>'
            for book in obj.book_set.all()
        )
        return format_html(links)

    display_books.short_description = "Books"


class SeriesBookInline(admin.TabularInline):
    model = Series.books.through
    extra = 1


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ("title", "book_count")
    inlines = [SeriesBookInline]

    def book_count(self, obj):
        return obj.books.count()

    book_count.short_description = "Book Count"


@admin.register(Changelog)
class ChangelogAdmin(admin.ModelAdmin):
    list_display = ("date", "summary")


admin.site.unregister(Group)
admin.site.register(BookReading)
admin.site.register(BookNote)
