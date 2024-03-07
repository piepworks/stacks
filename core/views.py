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
from .forms import RegisterForm, UserBookForm
from .utils import send_email_to_admin
from .models import UserBook
from django.db import models


def home(request):
    context = {}

    if request.user.is_authenticated:
        return redirect("status", status="backlog")

    return render(request, "home.html", context)


@login_required
def status(request, status):
    if status not in dict(UserBook._meta.get_field("status").choices):
        raise Http404()

    status_counts = (
        UserBook.objects.filter(user=request.user)
        .values("status")
        .annotate(count=models.Count("status"))
    )
    books = UserBook.objects.filter(user=request.user, status=status).order_by(
        "-updated_at"
    )

    context = {
        "statuses": UserBook._meta.get_field("status").choices,
        "status_counts": {
            status["status"]: status["count"] for status in status_counts
        },
        "books": books,
        "status": {
            "slug": status,
            "name": UserBook(status=status).get_status_display(),
        },
    }

    return render(request, "status.html", context)


@login_required
def userbook_new(request):
    if request.method == "POST":
        form = UserBookForm(request.POST)

        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            return redirect("userbook_detail", pk=book.pk)
    else:
        form = UserBookForm()

    return render(request, "userbook_form.html", {"form": form})


@login_required
def userbook_detail(request, pk):
    book = UserBook.objects.get(pk=pk, user=request.user)
    return render(request, "userbook_detail.html", {"book": book})


@login_required
def userbook_update(request, pk):
    book = UserBook.objects.get(pk=pk, user=request.user)
    statuses = UserBook._meta.get_field("status").choices
    old_status = book.status

    if request.method == "POST":
        form = UserBookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"{book.book} updated from {dict(statuses).get(old_status)} to {dict(statuses).get(book.status)}",
            )

            return redirect("status", status=book.status)
    else:
        form = UserBookForm(instance=book)

    return render(request, "userbook_form.html", {"form": form})


@require_POST
@login_required
def userbook_delete(request, pk):
    book = get_object_or_404(UserBook, pk=pk, user=request.user)
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
