from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic.base import RedirectView, TemplateView
from core import views
from core.forms import RegisterForm

admin.site.site_header = "Stacks Admin"
admin.site.site_title = "Stacks Admin"
admin.site.index_title = "Stacks innards"


urlpatterns = [
    path("", views.home, name="index"),
    path("status/<slug:status>", views.status, name="status"),
    # PWA goodies
    path(
        "sw.js",
        TemplateView.as_view(
            template_name="js/sw.js", content_type="application/javascript"
        ),
        name="sw",
    ),
    path("offline", TemplateView.as_view(template_name="offline.html"), name="offline"),
    # Logbook
    path("logbook", views.logbook, name="logbook"),
    # Book Imports
    # ------------
    path("import", views.import_books, name="import_books"),
    path("imports", views.imports, name="imports"),
    # Changelog
    # ---------
    path("changelog", views.changelog, name="changelog"),
    path("changelog/latest", views.changelog_latest, name="changelog_latest"),
    path("changelog/feed", views.ChangelogFeed(), name="changelog_feed"),
    # Book CRUD
    # ---------
    path("book/new", views.book_new, name="book_new"),  # C
    path("book/<int:pk>", views.book_detail, name="book_detail"),  # R
    path("book/<int:pk>/update", views.book_update, name="book_update"),  # U
    path("book/<int:pk>/delete", views.book_delete, name="book_delete"),  # D
    path("book/<int:pk>/archive", views.book_archive, name="book_archive"),
    path("book/<int:pk>/unarchive", views.book_unarchive, name="book_unarchive"),
    # Book Series
    # -----------
    path("series", views.series_list, name="series_list"),
    path("series/new", views.series_new, name="series_new"),  # C
    path("series/<int:pk>", views.series_detail, name="series_detail"),  # R
    path("series/<int:pk>/update", views.series_update, name="series_update"),  # U
    path("series/<int:pk>/delete", views.series_delete, name="series_delete"),  # D
    path("series/<int:pk>/add", views.series_add_book, name="series_add_book"),
    path("series/<int:pk>/remove", views.series_remove_book, name="series_remove_book"),
    # Book Search
    # -----------
    path("search", views.search, name="search"),
    path("ol", views.open_library_search, name="open_library_search"),
    # Authors
    # -------
    path("author/new", views.author_new, name="author_new"),  # C
    path("author/<int:pk>", views.author_detail, name="author_detail"),  # R
    path("author/<int:pk>/update", views.author_update, name="author_update"),  # U
    path("author/<int:pk>/delete", views.author_delete, name="author_delete"),  # D
    # Book Covers
    # -----------
    path("book/<int:pk>/cover/new", views.cover_new, name="cover_new"),
    path(
        "book/<int:pk>/cover/<int:cover_pk>/update",
        views.cover_update,
        name="cover_update",
    ),
    path(
        "book/<int:pk>/cover/<int:cover_pk>/delete",
        views.cover_delete,
        name="cover_delete",
    ),
    path(
        "book/<int:pk>/cover/<int:cover_pk>/order/<str:direction>",
        views.cover_order,
        name="cover_order",
    ),
    # Book Readings
    # -------------
    path("book/<int:pk>/reading/new", views.reading_new, name="reading_new"),
    path(
        "book/<int:pk>/reading/<int:reading_pk>/update",
        views.reading_update,
        name="reading_update",
    ),
    path(
        "book/<int:pk>/reading/<int:reading_pk>/delete",
        views.reading_delete,
        name="reading_delete",
    ),
    # Book Notes
    # ----------
    path("book/<int:pk>/note/new", views.note_new, name="note_new"),
    path(
        "book/<int:pk>/note/<int:note_pk>/update",
        views.note_update,
        name="note_update",
    ),
    path(
        "book/<int:pk>/note/<int:note_pk>/delete",
        views.note_delete,
        name="note_delete",
    ),
    # User settings
    path("settings", views.user_settings, name="settings"),
    # Boilerplate
    # -----------
    path("favicon.ico", views.favicon),
    # Redirect the old registration URL.
    path(
        "register/",
        RedirectView.as_view(pattern_name="django_registration_register"),
    ),
    # Redirect an authenticated user from the login page.
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path(
        "accounts/register/",
        views.RegistrationView.as_view(
            form_class=RegisterForm,
        ),
        name="django_registration_register",
    ),
    path(
        "accounts/activate/<str:activation_key>/",
        views.ActivationView.as_view(),
        name="django_registration_activate",
    ),
    path(
        "account-verified/<int:user_id>",
        views.account_verified,
        name="account-verified",
    ),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns = [
        path("__debug__/", include("debug_toolbar.urls")),
        path("__reload__/", include("django_browser_reload.urls")),
        path("404", TemplateView.as_view(template_name="404.html")),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
