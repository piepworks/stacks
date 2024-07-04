from django.shortcuts import get_object_or_404
from django.urls import reverse
from dateutil import parser
from datetime import date
from huey.contrib.djhuey import db_task
from .models import User, Book, BookCover, BookReading, Author
from .utils import pluralize
from .cover_helpers import search_open_library
from .import_helpers import (
    goodreads_status,
    the_storygraph_status,
    published_year_from_isbn,
)


@db_task()
def import_single_book(row, user_id):
    user = get_object_or_404(User, id=user_id)
    main_author = None
    additional_authors = []
    authors = []

    if row.get("Author"):
        # Goodreads
        main_author, created_author = Author.objects.get_or_create(
            name=row["Author"],
            user=user,
        )

        if row.get("Additional Authors", "").strip():
            for author in row["Additional Authors"].split(","):
                new_author, created_additional_author = Author.objects.get_or_create(
                    name=author,
                    user=user,
                )
                additional_authors.append(new_author)

    if row.get("Authors"):
        # The StoryGraph
        for author in row["Authors"].split(","):
            new_author, created_new_author = Author.objects.get_or_create(
                name=author,
                user=user,
            )
            authors.append(new_author)

    if row.get("Exclusive Shelf") or row.get("Bookshelves"):
        status = goodreads_status(
            row["Exclusive Shelf"]
            if row.get("Exclusive Shelf")
            else row.get("Bookshelves") if row.get("Bookshelves") else "to-read"
        )
    elif row.get("Read Status"):
        status = the_storygraph_status(
            row["Read Status"] if row.get("Read Status") else "to-read"
        )
    else:
        status = "wishlist"

    published_year = (
        row.get("Original Publication Year")
        if row.get("Original Publication Year")
        else row.get("Year Published") if row.get("Year Published") else None
    )

    if not published_year and row.get("ISBN/UID"):
        published_year = published_year_from_isbn(row["ISBN/UID"])

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
        if main_author:
            # Goodreads
            book.author.add(main_author.id)

        if additional_authors:
            # Goodreads
            book.author.add(*additional_authors)

        if authors:
            # The StoryGraph
            book.author.add(*authors)

        # Download a cover from Open Library
        cover_author = main_author if main_author else authors[0] if authors else None
        if cover_author:
            results = search_open_library(
                f"&title={book.title}&author={cover_author.name}"
            )
        else:
            results = search_open_library(f"&title={book.title}")

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
            # First, try to get a "Dates Read" (The StoryGraph) field with content like:
            # 2023/10/28-2024/01/24

            if dates_read := row.get("Dates Read"):
                start_date, end_date = dates_read.split("-")
                start_date = parser.parse(start_date)
                end_date = parser.parse(end_date)

                reading = BookReading.objects.create(
                    book=book,
                    start_date=start_date,
                    end_date=end_date,
                    finished=True,
                    rating=(
                        int(row.get("Star Rating")) if row.get("Star Rating") else None
                    ),
                )
                reading.save()
            else:
                # Goodreads fallback
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

    return False


@db_task()
def import_books_from_csv(data, user_id):
    user = get_object_or_404(User, id=user_id)

    tasks = [import_single_book(row, user_id) for row in data]
    results = [task_result.get(blocking=True) for task_result in tasks]
    count = results.count(True)

    user.email_user(
        subject="Book Stacks import finished!",
        message=(
            f"Your import of {count} {pluralize('book', count)} is done!\n\n"
            f"https://bookstacks.app{reverse('imports')}"  # noqa: E231
        ),
    )
