# Generated by Django 5.1.3 on 2024-11-21 18:38

import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_alter_book_author"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="book",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="book",
            constraint=models.UniqueConstraint(
                models.F("user"),
                django.db.models.functions.text.Lower("title"),
                name="user_title_unique",
            ),
        ),
    ]