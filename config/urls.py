from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView
from config.settings import ALLOWED_HOSTS
from core import views

urlpatterns = [
    path("", views.home, name="index"),
    path("status/<slug:status>", views.status, name="status"),
    # Books
    # --------
    path("book/new", views.book_new, name="book_new"),  # C
    path("book/<int:pk>", views.book_detail, name="book_detail"),  # R
    path("book/<int:pk>/update", views.book_update, name="book_update"),  # U
    path("book/<int:pk>/delete", views.book_delete, name="book_delete"),  # D
    # Boilerplate
    # -----------
    path("favicon.ico", views.favicon),
    path("register/", views.register, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        settings.ADMIN_URL,
        admin.site.urls,
        {"extra_context": {"ALLOWED_HOST": ALLOWED_HOSTS[0]}},
    ),
]

if settings.DEBUG:
    urlpatterns = [
        path("__debug__/", include("debug_toolbar.urls")),
        path("__reload__/", include("django_browser_reload.urls")),
        path("404", TemplateView.as_view(template_name="404.html")),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
