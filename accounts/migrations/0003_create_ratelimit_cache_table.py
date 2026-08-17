from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command("createcachetable", "django_cache", verbosity=0)


def drop_cache_table(apps, schema_editor):
    schema_editor.execute("DROP TABLE IF EXISTS django_cache")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_alter_user_email_alter_user_username"),
    ]

    operations = [
        migrations.RunPython(create_cache_table, drop_cache_table),
    ]
