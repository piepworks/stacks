import uuid
from django.utils.text import slugify
from PIL import Image
from config import settings


def resize_and_optimize_image(instance, image):
    if settings.DEBUG:
        # Open the image using PIL
        img = Image.open(f"media/{image}")

        # Resize the image to a max-width of 600px
        max_width = 600

        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height))
            img.save(f"media/{image}", format="JPEG", quality=60)

        return img
    else:
        return image


def rename_image(instance, filename):
    extension = filename.split(".")[-1]
    new_filename = slugify(instance.book.title.replace("/", ""))

    return f"stacks/covers/{new_filename}_{uuid.uuid4()}.{extension}"
