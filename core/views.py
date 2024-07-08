import io
import csv
import json
import bleach
import markdown
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login
from django.conf import settings
from django.urls import reverse
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.db import IntegrityError, models
from django.db.models import Q, OuterRef, Exists, Subquery, DateField
from django.db.models.functions import Trunc
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django_registration.backends.activation.views import (
    ActivationView as BaseActivationView,
    RegistrationView as BaseRegistrationView,
)
from honeypot.decorators import check_honeypot
from .forms import (
    ImportBooksForm,
    BookForm,
    BookStatusForm,
    BookReadingForm,
    BookCoverForm,
    BookNoteForm,
    AuthorForm,
    SettingsForm,
    OpenLibrarySearchForm,
)
from .utils import send_email_to_admin
from .cover_helpers import search_open_library
from .filter_helpers import get_filter_counts
from .models import (
    User,
    Book,
    Author,
    BookCover,
    BookFormat,
    BookReading,
    BookType,
    BookLocation,
    BookGenre,
)
from .tasks import import_books_from_csv


def home(request):
    context = {}

    if request.user.is_authenticated:
        return redirect("status", status="reading")

    return render(request, "home.html", context)


@login_required
def status(request, status):
    if status not in dict(Book._meta.get_field("status").choices):
        raise Http404()

    books = (
        Book.objects.filter(status=status, archived=False, user=request.user)
        .order_by("-updated_at")
        .prefetch_related("covers", "author", "format", "genre", "location", "type")
    )

    # Check if genres/types have sub-genres/types
    sub_genre_exists = BookGenre.objects.filter(parent=OuterRef("pk")).values("pk")
    sub_type_exists = BookType.objects.filter(parent=OuterRef("pk")).values("pk")

    genres = BookGenre.objects.all().annotate(has_sub_genre=Exists(sub_genre_exists))
    types = BookType.objects.all().annotate(has_sub_type=Exists(sub_type_exists))

    # Determine which filter options have matching books

    locations = BookLocation.objects.all()
    formats = BookFormat.objects.all()

    # Fetch all books once
    all_books = list(
        books.values("type__slug", "location__slug", "format__slug", "genre__slug")
    )

    type_filters = {
        type.slug: any(book["type__slug"] == type.slug for book in all_books)
        for type in types
    }
    location_filters = {
        location.slug: any(
            book["location__slug"] == location.slug for book in all_books
        )
        for location in locations
    }
    format_filters = {
        format.slug: any(book["format__slug"] == format.slug for book in all_books)
        for format in formats
    }
    genre_filters = {
        genre.slug: any(book["genre__slug"] == genre.slug for book in all_books)
        for genre in genres
    }

    # Get filter counts before applying filters
    filter_counts = {
        "type": get_filter_counts(books, types, "type"),
        "genre": get_filter_counts(books, genres, "genre"),
        "location": get_filter_counts(books, locations, "location"),
        "format": get_filter_counts(books, formats, "format"),
    }

    # Get filter parameters from request
    filter_queries = {
        "type": request.GET.get("type", "all"),
        "location": request.GET.get("location", "all"),
        "format": request.GET.get("format", "all"),
        "genre": request.GET.get("genre", "all"),
    }

    # Apply filters to the books queryset
    try:
        if filter_queries["type"] != "all":
            # Get the type
            type = BookType.objects.get(slug=filter_queries["type"])
            # If the type is a parent, also check for child types within this type
            if not type.parent:
                child_types = BookType.objects.filter(parent=type)
                books = books.filter(Q(type=type) | Q(type__in=child_types))
            else:
                books = books.filter(type=type)
        if filter_queries["genre"] != "all":
            # Get the genre
            genre = BookGenre.objects.get(slug=filter_queries["genre"])
            # If the genre has a parent, also check for sub-genres within this genre
            if not genre.parent:
                child_genres = BookGenre.objects.filter(parent=genre)
                books = books.filter(Q(genre=genre) | Q(genre__in=child_genres))
            else:
                books = books.filter(genre=genre)
    except (BookType.DoesNotExist, BookGenre.DoesNotExist):
        raise Http404()
    if filter_queries["location"] != "all":
        books = books.filter(location__slug=filter_queries["location"])
    if filter_queries["format"] != "all":
        books = books.filter(format__slug=filter_queries["format"])

    # Sort these statuses by the end date of their latest reading
    if status in ["finished", "dnf"]:
        latest_bookreading = BookReading.objects.filter(
            Q(book=OuterRef("pk"))
            & (Q(finished=True) if status == "finished" else Q(finished=False))
        ).order_by("-start_date")
        books = books.annotate(
            latest_reading_end_date=Subquery(latest_bookreading.values("end_date")[:1])
        ).order_by("-latest_reading_end_date")

    paginator = Paginator(books, 30)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # If status is `finished`, get counts of how many (unique?) Books have
    # associated BookReadings that have end dates in each year and are also
    # marked finished
    #
    # Books of any status can have a reading that's finished
    # This is so you can re-read a book and have it count as finished
    # while still being counted as being finished before.

    if status == "finished":
        finished_counts = (
            Book.objects.filter(
                user=request.user,
                readings__end_date__isnull=False,
                readings__finished=True,
            )
            .values("readings__end_date__year")
            .annotate(count=models.Count("readings__end_date__year"))
        )

    # Get the books and their forms for the page
    forms = [(book, BookStatusForm(instance=book)) for book in page_obj]

    status_counts = {
        status["status"]: status["count"]
        for status in Book.objects.filter(user=request.user, archived=False)
        .values("status")
        .annotate(count=models.Count("status"))
    }

    books_count = books.count()

    context = {
        "statuses": Book._meta.get_field("status").choices,
        "status_counts": status_counts,
        "finished_counts": finished_counts if status == "finished" else None,
        "status": {
            "slug": status,
            "name": Book(status=status).get_status_display(),
        },
        "forms": forms,
        "open_library_search_form": OpenLibrarySearchForm,
        "formats": formats,
        "types": types,
        "locations": locations,
        "genres": genres,
        "page_obj": page_obj,
        "type_filters": type_filters,
        "location_filters": location_filters,
        "format_filters": format_filters,
        "genre_filters": genre_filters,
        "filter_queries": filter_queries,
        "filter_active": status_counts.get(status, 0) != books_count,
        "filter_request": any(value != "all" for value in filter_queries.values()),
        "filter_counts": filter_counts,
        "filtered_books_count": books_count,
    }

    if request.htmx:
        return render(request, "components/book-list.html", context)
    else:
        return render(request, "status.html", context)


@login_required
def import_books(request):
    if request.method == "POST":
        form = ImportBooksForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = request.FILES["csv"]

            if not csv_file.name.endswith(".csv"):
                messages.error(request, "Please choose a CSV file.")
                return redirect(reverse("import_books"))

            data = csv_file.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(data))

            import_books_from_csv(list(reader), request.user.id)

        else:
            messages.error(request, "Nope.")
            reader = False

        if not reader:
            return redirect(reverse("import_books"))

        messages.success(
            request, "Import started. We’ll send you an email when it's done."
        )
        return redirect("index")

    return render(request, "import_books.html", {"form": ImportBooksForm})


@login_required
def imports(request):
    # Group books by date and retrieve all details
    books = (
        request.user.books.filter(imported=True)
        .annotate(date_imported=Trunc("created_at", "day", output_field=DateField()))
        .order_by("-date_imported")
    )

    # Structure the data for the template
    imports_grouped_by_date = {}
    for book in books:
        date = book.date_imported
        if date not in imports_grouped_by_date:
            imports_grouped_by_date[date] = {"books": [book], "count": 1}
        else:
            imports_grouped_by_date[date]["books"].append(book)
            imports_grouped_by_date[date]["count"] += 1

    # Convert the dictionary to a list of tuples for easier template iteration
    imports_grouped_by_date = sorted(
        imports_grouped_by_date.items(), key=lambda x: x[0], reverse=True
    )

    context = {
        "imports_grouped_by_date": imports_grouped_by_date,
    }

    return render(request, "imports.html", context)


@login_required
def book_new(request):
    if request.method == "POST":
        form = BookForm(request.POST, user=request.user)

        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user

            if (olid := request.POST.get("olid")) != "":
                book.olid = olid

            try:
                book.save()
                form.save_m2m()
            except IntegrityError:
                form.add_error("title", "You already have a book with this title")
                return render(
                    request,
                    "book_form.html",
                    {
                        "form": form,
                        "olid": book.olid,
                        "cover": "",
                        "action": "new",
                    },
                )

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

        form = BookForm(user=request.user)

        # If there's a querystring for status, set the initial value
        if "status" in request.GET:
            form.fields["status"].initial = request.GET["status"]

        for a in authors:
            if not a:
                # Don't save an empty author
                continue
            if not Author.objects.filter(name=a, user=request.user.id).exists():
                new_author = Author.objects.create(
                    name=a,
                    user=request.user,
                )
                author_records.append(new_author)
            else:
                author_records.append(Author.objects.get(name=a, user=request.user.id))

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
    book = get_object_or_404(Book, pk=pk, user=request.user)
    notes = book.notes.all()
    status_changes = book.status_changes.all()

    # Apply Markdown formatting and convert URLs in notes to clickable links
    for note in notes:
        note.text_html = bleach.linkify(
            markdown.markdown(note.text, extensions=["fenced_code", "smarty"])
        )

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
            "status_changes": status_changes,
            "notes": notes,
        },
    )


@login_required
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    old_status = book.status

    if request.method == "POST":
        form = BookForm(request.POST, instance=book, user=request.user)
        if form.is_valid():
            form.save()

            if request.POST.get("status_change"):
                messages.success(
                    request,
                    f"{book} moved to {book.get_status_display()}",
                )
                return redirect("status", status=old_status)

            messages.success(
                request,
                f"{book} updated",
            )

            return redirect(book.get_absolute_url())
    else:
        form = BookForm(instance=book, user=request.user)

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
    book = get_object_or_404(Book, pk=pk, user=request.user)
    status = book.status
    book.delete()
    messages.success(request, f"{book} deleted")
    return redirect("status", status=status)


@require_POST
@login_required
def book_archive(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    status = book.status
    book.archived = True
    book.save()
    messages.success(request, f"{book} archived")
    return redirect("status", status=status)


@login_required
def search(request):
    query = request.GET.get("q")
    if query:
        books = (
            Book.objects.filter(
                models.Q(title__icontains=query)
                | models.Q(author__name__icontains=query),
                user=request.user,
                author__user=request.user,
            )
            .exclude(archived=True)
            .distinct()
        )
    else:
        books = Book.objects.none()

    return render(
        request,
        "search.html",
        {
            "query": query,
            "books": books,
            "statuses": Book._meta.get_field("status").choices,
        },
    )


@login_required
def open_library_search(request):
    status = request.GET.get("status")
    form = OpenLibrarySearchForm(request.GET or None)

    if form.is_valid():
        title = form.cleaned_data.get("title")
        author = form.cleaned_data.get("author")
    else:
        messages.error(request, "Search for something")
        # Get back to where you once belonged
        return redirect(request.META.get("HTTP_REFERER", "status"))

    query = f"&title={title}"
    if author:
        query += f"&author={author}"

    results = search_open_library(query)

    if "error" in results:
        messages.error(request, results["error"])
        return redirect(reverse("book_new") + f"?status={status}")

    # If results is a dict, it means there was only one result
    if isinstance(results, dict):
        messages.info(request, "Open Library didn’t have a cover for this book")
        return redirect(
            reverse("book_new")
            + f"?title={results['title']}&authors={','.join(results['authors'])}"
            + f"&year={results['published']}&status={status}"
        )

    # Now we know there are multiple results with covers

    # Put all the authors in a comma separated string
    for result in results:
        result["authors_string"] = ",".join(result.get("authors", []))

    if not results:
        messages.error(request, "No results from Open Library")
        return redirect(reverse("book_new") + f"?status={status}")

    return render(
        request,
        "ol_search.html",
        {
            "form": form,
            "results": results,
            "status": status,
        },
    )


@require_POST
@login_required
def author_new(request):
    if not request.headers.get("Content-Type") == "application/json":
        # Require AJAX
        raise PermissionDenied()

    author = json.loads(request.body)
    a = Author.objects.create(
        name=author["name"],
        user=request.user,
    )
    messages.success(request, f"Author {author['name']} added")
    return JsonResponse({"id": a.pk})


@login_required
def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk, user=request.user)
    books = Book.objects.filter(author=author)

    return render(
        request,
        "author_detail.html",
        {
            "author": author,
            "books": books,
        },
    )


@login_required
def author_update(request, pk):
    author = get_object_or_404(Author, pk=pk, user=request.user)

    if request.method == "POST":
        form = AuthorForm(request.POST, instance=author)

        if form.is_valid():
            form.save()
            messages.success(request, "Author updated")
            return redirect(author.get_absolute_url())

    else:
        form = AuthorForm(instance=author)

    return render(
        request,
        "author_form.html",
        {
            "author": author,
            "form": form,
            "action": "update",
        },
    )


@login_required
def cover_new(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)

    if request.method == "POST":
        form = BookCoverForm(request.POST, request.FILES, book=book)

        if form.is_valid():
            cover = form.save(commit=False)
            cover.book = book
            cover.save()
            messages.success(request, "Cover added")
            return redirect(book.get_absolute_url())

    else:
        form = BookCoverForm(book=book)

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
    book = get_object_or_404(Book, pk=pk, user=request.user)
    cover = BookCover.objects.get(pk=cover_pk, book=book)

    if request.method == "POST":
        form = BookCoverForm(request.POST, request.FILES, instance=cover)

        if form.is_valid():
            form.save()
            messages.success(request, "Cover updated")
            return redirect(book.get_absolute_url())

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
    cover = get_object_or_404(BookCover, pk=cover_pk, book=Book.objects.get(pk=pk))
    cover.delete()
    messages.success(request, "Cover deleted")
    return redirect("book_detail", pk=pk)


@login_required
def reading_new(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)

    if request.method == "POST":
        form = BookReadingForm(request.POST)

        if form.is_valid():
            reading = form.save(commit=False)
            reading.book = book
            reading.save()
            messages.success(request, "Reading added")
            return redirect(book.get_absolute_url())

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
    book = get_object_or_404(Book, pk=pk, user=request.user)
    reading = book.readings.get(pk=reading_pk)

    if request.method == "POST":
        form = BookReadingForm(request.POST, instance=reading)

        if form.is_valid():
            form.save()
            messages.success(request, "Reading updated")
            return redirect(book.get_absolute_url())

    else:
        form = BookReadingForm(instance=reading)

    return render(
        request,
        "reading_form.html",
        {
            "book": book,
            "reading": reading,
            "form": form,
            "action": "update",
        },
    )


@require_POST
@login_required
def reading_delete(request, pk, reading_pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    reading = book.readings.get(pk=reading_pk)
    reading.delete()
    messages.success(request, "Reading deleted")
    return redirect("book_detail", pk=pk)


@login_required
def note_new(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)

    if request.method == "POST":
        form = BookNoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.book = book
            note.save()
            messages.success(request, "Note added")
            return redirect(book.get_absolute_url() + "#heading-notes")

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
    book = get_object_or_404(Book, pk=pk, user=request.user)
    note = book.notes.get(pk=note_pk)

    if request.method == "POST":
        form = BookNoteForm(request.POST, instance=note)

        if form.is_valid():
            form.save()
            messages.success(request, "Note updated")
            return redirect(book.get_absolute_url())

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
    book = get_object_or_404(Book, pk=pk, user=request.user)
    note = book.notes.get(pk=note_pk)
    note.delete()
    messages.success(request, "Note deleted")
    return redirect("book_detail", pk=pk)


# ----------------------------------
# Standard stuff unrelated to books:
# ----------------------------------


@login_required
def user_settings(request):
    if request.method == "POST":
        form = SettingsForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated")
            return redirect("settings")
        else:
            context = {"form": form}
            return render(request, "settings.html", context)
    else:
        form = SettingsForm(instance=request.user)
        context = {"form": form}
        return render(request, "settings.html", context)


@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # One day
def favicon(request):
    file = (settings.BASE_DIR / "static" / "img" / "seahorse-64x64.png").open("rb")
    return FileResponse(file)


def account_verified(request, user_id):
    user = get_object_or_404(User, id=user_id)

    send_email_to_admin(
        subject=f"New Stacks user: {user.email}",
        message="EOM",
    )

    login(request, user)
    messages.success(request, "Your account has been activated! Enjoy!")
    return redirect("index")


class ActivationView(BaseActivationView):
    def get_success_url(self, user):
        return reverse("account-verified", args=(user.id,))


@method_decorator(check_honeypot, name="post")
class RegistrationView(BaseRegistrationView):
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect("index")
        return super().get(request, *args, **kwargs)
