# Generated by Django 5.1.1 on 2024-09-28 13:31

import core.image_helpers
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_alter_bookcover_thumbnail"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookcover",
            name="image_height",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bookcover",
            name="image_width",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="bookcover",
            name="image",
            field=models.ImageField(
                blank=True,
                height_field="image_height",
                null=True,
                upload_to=core.image_helpers.rename_image,
                width_field="image_width",
            ),
        ),
    ]
