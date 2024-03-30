import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker
from core.models import (
    Author,
    Book,
    BookCover,
    BookReading,
    BookNote,
    BookFormat,
    BookType,
    BookGenre,
    BookLocation,
)
from core.forms import BookCoverForm
from random import randint


class Command(BaseCommand):
    help = "Create random stuff to seed the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--num",
            type=int,
            default=10,
            help="Number of books and authors to create (default: 10)",
        )

    def handle(self, *args, **kwargs):
        fake = Faker()
        num_books_authors = kwargs["num"]
        formats = list(BookFormat.objects.all())

        # Delete all BookCover records and their associated images
        for cover in BookCover.objects.all():
            cover.image.delete()
        BookCover.objects.all().delete()

        Author.objects.all().delete()
        Book.objects.all().delete()

        # Create Books and Authors
        for _ in range(num_books_authors):
            author_name = fake.unique.name()
            author_slug = author_name.replace(" ", "-").lower()
            Author.objects.create(name=author_name, slug=author_slug, bio=fake.text())

            book_title = fake.unique.catch_phrase()
            book_slug = slugify(book_title)
            Book.objects.create(
                title=book_title,
                slug=book_slug,
                status=fake.random_element(
                    elements=(
                        "wishlist",
                        "backlog",
                        "to-read",
                        "reading",
                        "finished",
                        "dnf",
                    )
                ),
                type=fake.random_element(elements=BookType.objects.all()),
                genre=fake.random_element(elements=BookGenre.objects.all()),
                published_year=fake.year(),
            )

        for book in Book.objects.all():
            # Associate an existing Author with every Book
            author = Author.objects.order_by("?").first()
            book.author.add(author)

            # Download a Cover for every Book
            image_url = requests.get("https://source.unsplash.com/random").url
            cover_form = BookCoverForm({"url": image_url}, book=book)
            if cover_form.is_valid():
                cover = cover_form.save()
                cover.save()

            # Add a Format to every Book
            book.format.add(fake.random_element(formats))

            # Add a Location to every Book
            book.location.add(fake.random_element(BookLocation.objects.all()))

        # Create BookReadings for every Book
        for book in Book.objects.all():
            start_date = fake.date_between(start_date="-1y", end_date="today")
            end_date = None
            if randint(0, 1):
                end_date = fake.date_between(start_date=start_date, end_date="today")
            finished = bool(randint(0, 1))
            rating = None
            if finished:
                rating = randint(1, 5)
            BookReading.objects.create(
                book=book,
                start_date=start_date,
                end_date=end_date,
                finished=finished,
                rating=rating,
            )

        # Create BookNotes for every Book
        for book in Book.objects.all():
            for _ in range(5):
                BookNote.objects.create(
                    book=book,
                    text=fake.text(),
                    page=fake.random_int(min=1, max=500),
                    percentage=fake.random_int(min=1, max=100),
                )
