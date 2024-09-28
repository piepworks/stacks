from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import BookCover


class Command(BaseCommand):
    help = "Get dimensions for covers without them"

    def handle(self, *args, **kwargs):
        covers_without_dimensions = BookCover.objects.filter(
            Q(thumbnail_width__isnull=True)
            | Q(thumbnail_height__isnull=True)
            | Q(image_width__isnull=True)
            | Q(image_height__isnull=True)
        )
        for cover in covers_without_dimensions:
            cover.save()
        print(f"{covers_without_dimensions.count()} updated")
