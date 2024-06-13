import requests
from django.core.management.base import BaseCommand
from model_bakery import baker
from faker import Faker
from core.models import (
    User,
    Author,
    Book,
    BookCover,
    BookReading,
    BookNote,
    BookFormat,
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
        trey = User.objects.get(id=1)
        fake = Faker()
        num_books_authors = kwargs["num"]
        all_formats = BookFormat.objects.all()
        all_locations = BookLocation.objects.all()

        # Delete all BookCover records and their associated images
        for cover in BookCover.objects.all():
            cover.image.delete()
        BookCover.objects.all().delete()

        Author.objects.all().delete()
        Book.objects.all().delete()

        # Create Books and Authors
        for _ in range(num_books_authors):
            baker.make(Author, user=trey, name=fake.name(), bio=fake.text())
            baker.make(Book, user=trey, title=fake.sentence())

        for book in Book.objects.all():
            # Associate an existing Author with every Book
            author = Author.objects.order_by("?").first()
            book.author.add(author)

            # Download a Cover for every Book
            image_url = requests.get("https://picsum.photos/400/600").url
            cover_form = BookCoverForm({"url": image_url}, book=book)
            if cover_form.is_valid():
                cover = cover_form.save()
                cover.save()

            # Add one or more Formats to every Book
            num_formats = randint(1, 3)
            for _ in range(num_formats):
                book.format.add(fake.random_element(all_formats))

            # Add a Location to every Book
            num_locations = randint(1, 3)
            for _ in range(num_locations):
                book.location.add(fake.random_element(all_locations))

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
