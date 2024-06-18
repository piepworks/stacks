from django.shortcuts import get_object_or_404
from dateutil import parser
from datetime import date
from celery import shared_task
from celery.utils.log import get_task_logger
from .models import User, Book, BookCover, BookReading, Author
from .cover_helpers import search_open_library
from .import_helpers import goodreads_status

logging = get_task_logger(__name__)


@shared_task
def import_single_book(row, user_id):
    user = get_object_or_404(User, id=user_id)
    main_author, created_author = Author.objects.get_or_create(
        name=row["Author"],
        user=user,
    )
    additional_authors = []

    if row.get("Additional Authors", "").strip():
        for author in row["Additional Authors"].split(","):
            new_author, created_additional_author = Author.objects.get_or_create(
                name=author,
                user=user,
            )
            additional_authors.append(new_author)

    status = goodreads_status(
        row["Exclusive Shelf"]
        if row.get("Exclusive Shelf")
        else row.get("Bookshelves") if row.get("Bookshelves") else "to-read"
    )
    published_year = (
        row.get("Original Publication Year")
        if row.get("Original Publication Year")
        else row.get("Year Published") if row.get("Year Published") else None
    )

    book, created_book = Book.objects.get_or_create(
        title=row["Title"],
        user=user,
        defaults={
            "status": status,
            "published_year": published_year,
        },
    )

    # This is a book we didn't already have
    if created_book:
        book.imported = True
        book.save()
        book.author.add(main_author.id)

        if additional_authors:
            book.author.add(*additional_authors)

        # Download a cover from Open Library
        results = search_open_library(f"&title={book.title}&author={main_author.name}")
        if results:
            if isinstance(results, dict):
                # If there's only one result, it's a dict
                r = results
            else:
                # Get the first one and hope for the best
                r = results[0]

            olid = r.get("olid")
            if olid:
                book.olid = olid
                book.save()

            if "cover" in r:
                new_cover = BookCover.objects.create(
                    book=book,
                )
                saved_cover = new_cover.save_cover_from_url(r["cover"])
                if not saved_cover:
                    new_cover.delete()

        # Set reading based on the status
        if status == "reading":
            reading = BookReading.objects.create(
                book=book,
                start_date=parser.parse(row.get("Date Added")),
            )
            reading.save()

        if status == "finished":
            try:
                start_date = parser.parse(row.get("Date Added"))
                end_date = parser.parse(row.get("Date Read"))

                if start_date > end_date:
                    start_date = end_date
            except (TypeError, ValueError):
                start_date = date.today()
                end_date = date.today()

            reading = BookReading.objects.create(
                book=book,
                start_date=start_date,
                end_date=end_date,
                finished=True,
                rating=row.get("My Rating") or None,
            )
            reading.save()

        # Add review as a note if there is one
        if review := row.get("My Review"):
            note = book.notes.create(
                text=review,
            )
            note.save()

        return True
    else:
        return False


@shared_task
def import_from_goodreads(data, user_id):
    user = get_object_or_404(User, id=user_id)
    count = 0

    for row in data:
        created = import_single_book(row, user_id)

        if created:
            count += 1

    # Send an email to the user when import is done
    user.email_user(
        subject="Book Stacks import finished!",
        message=f"Your import of {count} books from Goodreads is done",
    )

    return f"{count} books imported"
