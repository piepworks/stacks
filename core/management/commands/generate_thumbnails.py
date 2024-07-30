from django.core.management.base import BaseCommand
from core.models import BookCover
from core.image_helpers import resize_image


class Command(BaseCommand):
    help = "Generate thumbnails for covers without one"

    def handle(self, *args, **kwargs):
        covers_without_thumbnails = BookCover.objects.filter(thumbnail__isnull=True)
        for cover in covers_without_thumbnails:
            cover.thumbnail = resize_image(cover.image, width=300)
            cover.save()
            self.stdout.write(
                self.style.SUCCESS(f"Thumbnail generated for book ID {cover.book.id}")
            )
