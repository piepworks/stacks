import uuid
from django.utils.text import slugify


def rename_image(instance, filename):
    extension = filename.split(".")[-1]
    new_filename = slugify(instance.book.title.replace("/", ""))

    return f"stacks/covers/{new_filename}_{uuid.uuid4()}.{extension}"
