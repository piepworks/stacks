# Generated by Django 5.0.3 on 2024-03-18 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_bookformat_remove_book_on_hand_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="format",
            field=models.ManyToManyField(
                blank=True,
                help_text="Choose as many as you have",
                related_name="books",
                to="core.bookformat",
            ),
        ),
    ]