"""Make auth_user.username unique without regard to case.

The registration form rejects a case variant of an existing name, but it is not
the only way a user is created: the admin, a management shell, and two
registrations racing each other all go around it. Under MySQL that never
mattered, because a case-insensitive collation makes the column's own UNIQUE
constraint case-insensitive too. On a case-sensitive engine the guarantee has
to be stated.

A functional index is the only way to express it here. UniqueConstraint over an
expression needs Django 4.0, and auth_user belongs to django.contrib.auth, so
it cannot carry a Meta constraint of ours in any case.
"""
from django.db import migrations


INDEX_NAME = 'auth_user_username_lower_uniq'


def create_index(apps, schema_editor):
    # MySQL 5.7 has no functional indexes, and needs none: its case-insensitive
    # collation already covers the existing UNIQUE on the column.
    if schema_editor.connection.vendor == 'mysql':
        return

    schema_editor.execute(
        'CREATE UNIQUE INDEX %s ON auth_user (LOWER(username))' % INDEX_NAME)


def drop_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'mysql':
        return

    schema_editor.execute('DROP INDEX %s' % INDEX_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        # The conversion applies this one on its way past; depending on it
        # keeps the ordering explicit rather than incidental.
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_index, drop_index),
    ]
