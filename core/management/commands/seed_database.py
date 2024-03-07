import requests
import urllib

from django.core.management.base import BaseCommand
from faker import Faker
from core.models import Author, Book, BookCover, rename_image


class Command(BaseCommand):
    help = "Create random stuff to seed the database"

    def handle(self, *args, **kwargs):
        fake = Faker()

        Author.objects.all().delete()
        Book.objects.all().delete()

        for _ in range(10):
            author_name = fake.unique.name()
            author_slug = author_name.replace(" ", "-").lower()
            Author.objects.create(name=author_name, slug=author_slug, bio=fake.text())

            book_title = fake.unique.catch_phrase()
            book_slug = book_title.replace(" ", "-").lower()
            Book.objects.create(
                title=book_title,
                slug=book_slug,
                published_year=fake.year(),
            )

        # Associate an existing Author with every Book
        for book in Book.objects.all():
            author = Author.objects.order_by("?").first()
            book.author.add(author)

        for cover in BookCover.objects.all():
            cover.image.delete()
        BookCover.objects.all().delete()

        # Download a Cover for every Book
        for book in Book.objects.all():
            cover = BookCover.objects.create(book=book)

            image_url = requests.get("https://source.unsplash.com/random").url
            # Get file name from `image_url` and remove any query parameters
            image_name = image_url.split("/")[-1].split("?")[0]
            image_name_final = f"{rename_image(cover, image_name)}.jpg"

            urllib.request.urlretrieve(image_url, f"media/{image_name_final}")
            cover.image = image_name_final
            cover.save()

        # For every Book, create a UserBook record for user pk 1
        for book in Book.objects.all():
            book.userbook_set.create(
                user_id=1,
                book_id=book.id,
                status=fake.random_element(
                    elements=("backlog", "to-read", "reading", "finished", "dnf")
                ),
                on_hand=fake.boolean(chance_of_getting_true=50),
            )
