# Generated by Django 5.1.1 on 2024-09-08 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_bookreading_review"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="olid",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="Open Library ID"
            ),
        ),
    ]