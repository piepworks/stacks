# Generated by Django 5.0.7 on 2024-08-05 19:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_series_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="series",
            options={"ordering": ["-updated_at"], "verbose_name_plural": "Series"},
        ),
    ]