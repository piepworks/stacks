# Generated by Django 5.0.7 on 2024-07-14 19:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0050_remove_book_genre"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="bookgenre",
            options={"ordering": ["parent__name", "name"]},
        ),
    ]