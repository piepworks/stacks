from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group
from .models import User, Book, Author, BookCover, BookReading, BookNote, BookFormat


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
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
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


class BookCoverInline(admin.TabularInline):
    model = BookCover
    extra = 1


class BookAuthorInline(admin.TabularInline):
    verbose_name = "Author"
    model = Book.author.through
    extra = 1


class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "authors_list")
    inlines = [BookAuthorInline, BookCoverInline]
    exclude = ("author",)
    prepopulated_fields = {"slug": ("title",)}

    def authors_list(self, obj):
        return ", ".join([author.name for author in obj.author.all()])

    authors_list.short_description = "Authors"


class BookFormatAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug")


class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug", "book_count")

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


admin.site.unregister(Group)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BookFormat, BookFormatAdmin)
admin.site.register(BookCover)
admin.site.register(BookReading)
admin.site.register(BookNote)
