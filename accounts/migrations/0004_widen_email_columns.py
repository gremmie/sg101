"""Widen two EmailField columns that never got Django 1.8's change.

Django widened EmailField's default max_length from 75 to 254 in 1.8.
auth_user.email picked that up through Django's own migration, but these two
columns did not, because their app had no migrations to carry it. models.py
has said 254 for years while the database says 75.

Simply re-asserting the field does not work, and the reason is worth stating:
0001_initial was generated from the models during the migration backfill, so
it already declares 254, and it was applied with --fake-initial against tables
that really are varchar(75). Django therefore believes the columns are already
254 and an AlterField to 254 emits no SQL at all -- it reports OK and changes
nothing.

So the recorded state is first corrected to 75 without touching the database,
and only then altered to 254, which is a real change Django will emit. The
final state still matches models.py, so makemigrations --check stays clean.

Written by hand rather than as a pgloader CAST rule because it is
engine-agnostic, survives a re-run of the conversion, applies to MySQL just as
well, and leaves the reason in the migration history.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_normalize_case_variant_emails'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # State only: tell Django what the columns really are, so that the
            # widening below is a change it can see.
            state_operations=[
                migrations.AlterField(
                    model_name='illegalemail',
                    name='email',
                    field=models.EmailField(db_index=True, max_length=75),
                ),
                migrations.AlterField(
                    model_name='pendinguser',
                    name='email',
                    field=models.EmailField(max_length=75),
                ),
            ],
            database_operations=[],
        ),
        migrations.AlterField(
            model_name='illegalemail',
            name='email',
            field=models.EmailField(db_index=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='email',
            field=models.EmailField(max_length=254),
        ),
    ]
