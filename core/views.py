import json
import bleach
import markdown
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
from django.db import models
from django.utils.text import slugify
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .forms import (
    RegisterForm,
    BookForm,
    BookStatusForm,
    BookReadingForm,
    BookCoverForm,
    BookNoteForm,
)
from .utils import send_email_to_admin
from .cover_helpers import search_open_library
from .models import Book, Author, BookCover


def home(request):
    context = {}

    if request.user.is_authenticated:
        return redirect("status", status="reading")

    return render(request, "home.html", context)


@login_required
def status(request, status):
    if status not in dict(Book._meta.get_field("status").choices):
        raise Http404()

    status_counts = (
        Book.objects.all().values("status").annotate(count=models.Count("status"))
    )
    books = Book.objects.filter(status=status).order_by("-updated_at")
    forms = [(book, BookStatusForm(instance=book)) for book in books]

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
        "status": {
            "slug": status,
            "name": Book(status=status).get_status_display(),
        },
        "forms": forms,
    }

    return render(request, "status.html", context)


@login_required
def book_new(request):
    if request.method == "POST":
        form = BookForm(request.POST)

        if form.is_valid():
            book = form.save(commit=False)

            if (olid := request.POST.get("olid")) != "":
                book.olid = olid

            book.save()
            form.save_m2m()

            if cover := request.POST.get("cover"):
                new_cover = BookCover.objects.create(
                    book=book,
                )
                new_cover.save_cover_from_url(cover)

            messages.success(request, f"{book} added")
            return redirect("book_detail", pk=book.pk)
    else:
        olid = request.GET.get("olid", "")
        cover = request.GET.get("cover", "")
        authors = request.GET.get("authors", "").split(",")
        author_records = []
        title = request.GET.get("title", "")
        year = request.GET.get("year", "")

        form = BookForm()

        # If there's a querystring for status, set the initial value
        if "status" in request.GET:
            form.fields["status"].initial = request.GET["status"]

        for a in authors:
            if not a:
                # Don't save an empty author
                continue
            if not Author.objects.filter(slug=slugify(a)).exists():
                new_author = Author.objects.create(
                    name=a,
                    slug=slugify(a),
                )
                author_records.append(new_author)
            else:
                author_records.append(Author.objects.get(slug=slugify(a)))

        form.fields["author"].initial = author_records
        form.fields["title"].initial = title
        form.fields["published_year"].initial = year

    return render(
        request,
        "book_form.html",
        {
            "form": form,
            "olid": olid,
            "authors": authors,
            "cover": cover,
            "action": "new",
        },
    )


@login_required
def book_detail(request, pk):
    book = Book.objects.get(pk=pk)
    notes = book.notes.all()

    # Apply Markdown formatting and convert URLs in notes to clickable links
    for note in notes:
        note.text_html = bleach.linkify(markdown.markdown(note.text))

    return render(
        request,
        "book_detail.html",
        {
            "book": book,
            "status": {
                "slug": book.status,
                "name": book.get_status_display(),
            },
            "reading_form": BookReadingForm(instance=book),
            "note_form": BookNoteForm(instance=book),
            "readings": book.readings.all(),
            "notes": notes,
        },
    )


@login_required
def book_update(request, pk):
    book = Book.objects.get(pk=pk)
    # statuses = Book._meta.get_field("status").choices
    # old_status = book.status

    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()

            # TODO: customize message based on what was actually updated
            messages.success(
                request,
                f"{book} updated",
            )

            return redirect("book_detail", pk=book.id)
    else:
        form = BookForm(instance=book)

    return render(
        request,
        "book_form.html",
        {
            "book": book,
            "form": form,
            "action": "update",
        },
    )


@require_POST
@login_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, f"{book} deleted")
    return redirect("status", status="backlog")


@login_required
def search(request):
    query = request.GET.get("q")
    if query:
        books = Book.objects.filter(title__icontains=query)
    else:
        books = Book.objects.none()

    return render(
        request,
        "search.html",
        {
            "query": query,
            "books": books,
        },
    )


@login_required
def open_library_search(request):
    query = request.GET.get("q")
    status = request.GET.get("status")

    if not query:
        messages.error(request, "Search for something")
        # Get back to where you once belonged
        return redirect(request.META.get("HTTP_REFERER", "status"))

    results = search_open_library(query)

    # Put all the authors in a comma separated string
    for result in results:
        result["authors_string"] = ",".join(result.get("authors", []))

    if not results:
        messages.error(request, "No results from Open Library")
        return redirect(reverse("book_new") + f"?status={status}")

    return render(request, "ol_search.html", {"results": results, "status": status})


@require_POST
@login_required
def author_new(request):
    if not request.headers.get("Content-Type") == "application/json":
        # Require AJAX
        raise PermissionDenied()

    author = json.loads(request.body)
    slug = slugify(author["name"])
    a = Author.objects.create(
        name=author["name"],
        slug=slug,
    )
    messages.success(request, f"Author {author['name']} added")
    return JsonResponse({"id": a.pk})


@login_required
def cover_new(request, pk):
    book = Book.objects.get(pk=pk)

    if request.method == "POST":
        form = BookCoverForm(request.POST, request.FILES)

        if form.is_valid():
            cover = form.save(commit=False)
            cover.book = book
            cover.save()
            messages.success(request, "Cover added")
            return redirect("book_detail", pk=book.pk)

    else:
        form = BookCoverForm()

    return render(
        request,
        "cover_form.html",
        {
            "book": book,
            "form": form,
            "action": "new",
        },
    )


@login_required
def cover_update(request, pk, cover_pk):
    book = Book.objects.get(pk=pk)
    cover = BookCover.objects.get(pk=cover_pk, book=pk)

    if request.method == "POST":
        form = BookCoverForm(request.POST, request.FILES, instance=cover)

        if form.is_valid():
            form.save()
            messages.success(request, "Cover updated")
            return redirect("book_detail", pk=pk)

    else:
        form = BookCoverForm(instance=cover)

    return render(
        request,
        "cover_form.html",
        {
            "book": book,
            "form": form,
            "action": "update",
        },
    )


@require_POST
@login_required
def cover_delete(request, pk, cover_pk):
    cover = BookCover.objects.get(pk=cover_pk, book=pk)
    cover.delete()
    messages.success(request, "Cover deleted")
    return redirect("book_update", pk=pk)


@login_required
def reading_new(request, pk):
    book = Book.objects.get(pk=pk)

    if request.method == "POST":
        form = BookReadingForm(request.POST)

        if form.is_valid():
            reading = form.save(commit=False)
            reading.book = book
            reading.save()
            messages.success(request, "Reading added")
            return redirect("book_detail", pk=book.pk)

    else:
        form = BookReadingForm()

    return render(
        request,
        "reading_form.html",
        {
            "book": book,
            "form": form,
            "action": "new",
        },
    )


@login_required
def reading_update(request, pk, reading_pk):
    book = Book.objects.get(pk=pk)
    reading = book.readings.get(pk=reading_pk)

    if request.method == "POST":
        form = BookReadingForm(request.POST, instance=reading)

        if form.is_valid():
            form.save()
            messages.success(request, "Reading updated")
            return redirect("book_detail", pk=pk)

    else:
        form = BookReadingForm(instance=reading)

    return render(
        request,
        "reading_form.html",
        {
            "book": book,
            "form": form,
            "action": "update",
        },
    )


@require_POST
@login_required
def reading_delete(request, pk, reading_pk):
    reading = Book.objects.get(pk=pk).readings.get(pk=reading_pk)
    reading.delete()
    messages.success(request, "Reading deleted")
    return redirect("book_detail", pk=pk)


@login_required
def note_new(request, pk):
    book = Book.objects.get(pk=pk)

    if request.method == "POST":
        form = BookNoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.book = book
            note.save()
            messages.success(request, "Note added")
            return redirect("book_detail", pk=book.pk)

    else:
        form = BookNoteForm()

    return render(
        request,
        "note_form.html",
        {
            "book": book,
            "form": form,
            "action": "new",
        },
    )


@login_required
def note_update(request, pk, note_pk):
    book = Book.objects.get(pk=pk)
    note = book.notes.get(pk=note_pk)

    if request.method == "POST":
        form = BookNoteForm(request.POST, instance=note)

        if form.is_valid():
            form.save()
            messages.success(request, "Note updated")
            return redirect("book_detail", pk=pk)

    else:
        form = BookNoteForm(instance=note)

    return render(
        request,
        "note_form.html",
        {
            "book": book,
            "note": note,
            "form": form,
            "action": "update",
        },
    )


@require_POST
@login_required
def note_delete(request, pk, note_pk):
    note = Book.objects.get(pk=pk).notes.get(pk=note_pk)
    note.delete()
    messages.success(request, "Note deleted")
    return redirect("book_detail", pk=pk)


# ----------------------------------
# Standard stuff unrelated to books:
# ----------------------------------


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
