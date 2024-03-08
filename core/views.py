from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.urls import reverse
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from .forms import RegisterForm, BookForm
from .utils import send_email_to_admin
from .models import Book
from django.db import models
from django.utils.safestring import mark_safe


def home(request):
    context = {}

    if request.user.is_authenticated:
        return redirect("status", status="backlog")

    return render(request, "home.html", context)


@login_required
def status(request, status):
    if status not in dict(Book._meta.get_field("status").choices):
        raise Http404()

    status_counts = (
        Book.objects.all().values("status").annotate(count=models.Count("status"))
    )
    books = Book.objects.filter(status=status).order_by("-updated_at")

    # If status is `finished`, get counts of how many (unique?) Books have
    # associated BookReadings that have end dates in each year and are also
    # marked finished
    if status == "finished":
        finished_counts = (
            Book.objects.filter(
                readings__end_date__isnull=False,
                readings__finished=True,
            )
            .values("readings__end_date__year")
            .annotate(count=models.Count("readings__end_date__year"))
        )

    context = {
        "statuses": Book._meta.get_field("status").choices,
        "status_counts": {
            status["status"]: status["count"] for status in status_counts
        },
        "finished_counts": finished_counts if status == "finished" else None,
        "books": books,
        "status": {
            "slug": status,
            "name": Book(status=status).get_status_display(),
        },
    }

    return render(request, "status.html", context)


@login_required
def book_new(request):
    if request.method == "POST":
        form = BookForm(request.POST)

        if form.is_valid():
            book = form.save(commit=False)
            book.save()
            return redirect("book_detail", pk=book.pk)
    else:
        form = BookForm()

    return render(request, "book_form.html", {"form": form})


@login_required
def book_detail(request, pk):
    book = Book.objects.get(pk=pk)
    return render(request, "book_detail.html", {"book": book})


@login_required
def book_update(request, pk):
    book = Book.objects.get(pk=pk)
    statuses = Book._meta.get_field("status").choices
    old_status = book.status

    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                mark_safe(
                    f"""
                    <u>{book}</u> updated from <u>{dict(statuses).get(old_status)}</u>
                    to <u>{dict(statuses).get(book.status)}</u>
                    """
                ),
            )

            return redirect("status", status=book.status)
    else:
        form = BookForm(instance=book)

    return render(request, "book_form.html", {"form": form})


@require_POST
@login_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return redirect("status", status="backlog")


@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # One day
def favicon(request):
    file = (settings.BASE_DIR / "static" / "img" / "seahorse-64x64.png").open("rb")
    return FileResponse(file)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()

            # Automatically log in
            email = form.cleaned_data.get("email")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(email=email, password=raw_password)
            login(request, user)

            send_email_to_admin(
                subject="New portainer_stack user!",
                message=f"""{email} signed up!\n
                    https://{get_current_site(request)}{reverse('admin:core_user_changelist')}
                """,
            )

            return redirect("index")
    else:
        if request.user.is_authenticated:
            return redirect(reverse("index"))

        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})
