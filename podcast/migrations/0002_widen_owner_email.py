"""Widen Channel.owner_email, which never got Django 1.8's EmailField change.

Same story as accounts/0004, including the reason for the shape of it:
0001_initial was generated from the models during the backfill and already
declares 254, and it was faked against a table that is really varchar(75), so
an AlterField to 254 would report OK and emit nothing. The state is corrected
to 75 first, without touching the database, so the widening is a change Django
can actually see.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcast', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='channel',
                    name='owner_email',
                    field=models.EmailField(max_length=75),
                ),
            ],
            database_operations=[],
        ),
        migrations.AlterField(
            model_name='channel',
            name='owner_email',
            field=models.EmailField(max_length=254),
        ),
    ]
