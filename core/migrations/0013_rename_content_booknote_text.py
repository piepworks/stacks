# Generated by Django 5.0.3 on 2024-03-13 20:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_booknote"),
    ]

    operations = [
        migrations.RenameField(
            model_name="booknote",
            old_name="content",
            new_name="text",
        ),
    ]