# Generated by Django 5.1 on 2024-08-13 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_alter_series_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookreading",
            name="review",
            field=models.TextField(blank=True),
        ),
    ]