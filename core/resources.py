from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from .models import Author, Book, BookFormat, BookGenre, BookType


class BookResource(resources.ModelResource):
    # Handle foreign keys and many-to-many relationships
    author = fields.Field(
        column_name="authors",
        attribute="author",
        widget=ManyToManyWidget(Author, field="name", separator="|"),
    )

    format = fields.Field(
        column_name="formats",
        attribute="format",
        widget=ManyToManyWidget(BookFormat, field="name", separator="|"),
    )

    genre = fields.Field(
        column_name="genres",
        attribute="genre",
        widget=ManyToManyWidget(BookGenre, field="name", separator="|"),
    )

    type = fields.Field(
        column_name="type", attribute="type", widget=ForeignKeyWidget(BookType, "name")
    )

    # Add related readings
    readings = fields.Field()

    # Add related notes
    notes = fields.Field()

    def dehydrate_readings(self, book):
        readings = book.readings.all()
        return "\n".join(
            [
                f"Start: {r.start_date}, End: {r.end_date}, "
                f"Rating: {r.rating}, Review: {r.review}"
                for r in readings
            ]
        )

    def dehydrate_notes(self, book):
        notes = book.notes.all()
        return "\n".join([f"Page: {n.page}, Text: {n.text}" for n in notes])

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "published_year",
            "status",
            "type",
            "genre",
            "format",
            "pages",
            "olid",
            "readings",
            "notes",
        )
        export_order = fields

    def get_queryset(self):
        return self.Meta.model.objects.filter(user=self._meta.user).prefetch_related(
            "author", "format", "genre", "readings", "notes"
        )
