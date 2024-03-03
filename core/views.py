from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.urls import reverse
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from .forms import RegisterForm
from .utils import send_email_to_admin
from .models import BookExperience
from django.db import models


def home(request):
    context = {}

    if request.user.is_authenticated:
        context = {
            "statuses": BookExperience._meta.get_field("status").choices,
            "books": BookExperience.objects.filter(user=request.user).order_by(
                "status"
            ),
        }

    return render(request, "home.html", context)


@login_required
def status(request, status):
    status_counts = (
        BookExperience.objects.filter(user=request.user)
        .values("status")
        .annotate(count=models.Count("status"))
    )
    books = BookExperience.objects.filter(user=request.user, status=status)

    context = {
        "statuses": BookExperience._meta.get_field("status").choices,
        "status_counts": {
            status["status"]: status["count"] for status in status_counts
        },
        "books": books,
        "status": {
            "slug": status,
            "name": BookExperience(status=status).get_status_display(),
        },
    }

    return render(request, "status.html", context)


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
