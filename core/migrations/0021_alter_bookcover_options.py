# Generated by Django 5.0.3 on 2024-03-19 12:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_book_olid"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="bookcover",
            options={"ordering": ["-created_at"]},
        ),
    ]