import uuid
import io
import sys
from PIL import Image
from django.utils.text import slugify
from django.core.files.uploadedfile import InMemoryUploadedFile


def rename_image(instance, filename):
    extension = filename.split(".")[-1]
    new_filename = slugify(instance.book.title.replace("/", ""))

    return f"stacks/covers/{instance.book.user.id}_{new_filename}_{uuid.uuid4()}.{extension}"


def resize_image(image_file, width):
    with Image.open(image_file) as img:
        original_width, original_height = img.size
        new_height = int((width / original_width) * original_height)
        resized_img = img.resize((width, new_height), Image.LANCZOS)
        img_byte_arr = io.BytesIO()
        resized_img.save(img_byte_arr, format=img.format)
        img_byte_arr.seek(0)
        return InMemoryUploadedFile(
            img_byte_arr,
            "ImageField",
            image_file.name,
            "image/jpeg",
            sys.getsizeof(img_byte_arr),
            None,
        )
