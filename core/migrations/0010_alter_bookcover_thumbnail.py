# Generated by Django 5.1.1 on 2024-09-28 13:20

import core.image_helpers
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_bookcover_thumbnail_height_bookcover_thumbnail_width"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookcover",
            name="thumbnail",
            field=models.ImageField(
                blank=True,
                height_field="thumbnail_height",
                null=True,
                upload_to=core.image_helpers.rename_image,
                width_field="thumbnail_width",
            ),
        ),
    ]