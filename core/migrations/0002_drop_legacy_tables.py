"""Drop seven tables that no model has ever described.

They arrived with the MySQL-to-PostgreSQL conversion, which copied the old
database as it stood rather than pruning it -- a conversion is hard enough to
verify without also arguing about what should survive it. Two of the apps that
made them (`membermap`, `irc`) are gone, `auth_message` is Django's own message
table from before 1.4, `mailer_message` belonged to a mail queue this project
does not use, and `gcalendar_accesstoken` held the OAuth credential the calendar
stopped using when it moved to a service account. About 1,540 rows in total,
none of it read by anything.

`IF EXISTS` because most databases here never had them: a test database, or any
database built by running the migrations, starts from the models and so contains
none of these. Without it this migration would fail everywhere except the one
place it has work to do.

No `CASCADE`. Nothing currently references these tables -- the only foreign keys
run the other way, into `auth_user` -- and a table that turns out to have a
dependent should stop the migration rather than take the dependent with it.

Deliberately irreversible. Recreating seven empty tables would restore the shape
and none of the contents, which is a worse answer than an error: the rows exist
in the MySQL database this one was converted from, and that is where they would
have to come from.
"""
from django.db import migrations

LEGACY_TABLES = [
    'auth_message',
    'core_anonlastvisit',
    'core_userlastvisit',
    'gcalendar_accesstoken',
    'irc_ircchannel',
    'mailer_message',
    'membermap_mapentry',
]


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=['DROP TABLE IF EXISTS "%s";' % table for table in LEGACY_TABLES],
        ),
    ]
