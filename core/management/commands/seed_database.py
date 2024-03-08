import requests
import urllib
from django.core.management.base import BaseCommand
from faker import Faker
from core.models import Author, Book, BookCover, BookReading, rename_image
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
            book_slug = book_title.replace(" ", "-").lower()
            Book.objects.create(
                title=book_title,
                slug=book_slug,
                status=fake.random_element(
                    elements=("backlog", "to-read", "reading", "finished", "dnf")
                ),
                published_year=fake.year(),
            )

        # Associate an existing Author with every Book
        for book in Book.objects.all():
            author = Author.objects.order_by("?").first()
            book.author.add(author)

        # Download a Cover for every Book
        for book in Book.objects.all():
            cover = BookCover.objects.create(book=book)

            image_url = requests.get("https://source.unsplash.com/random").url
            # Get file name from `image_url` and remove any query parameters
            image_name = image_url.split("/")[-1].split("?")[0]
            image_name_final = f"{rename_image(cover, image_name)}.jpg"
            # Download the image to the media folder
            urllib.request.urlretrieve(image_url, f"media/{image_name_final}")
            cover.image = image_name_final
            cover.save()

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
            format_choices = ["physical", "digital", "audio"]
            format = format_choices[randint(0, 2)]
            BookReading.objects.create(
                book=book,
                start_date=start_date,
                end_date=end_date,
                finished=finished,
                rating=rating,
                format=format,
            )
