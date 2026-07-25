"""
Create the SG101 schema on an empty PostgreSQL database.

A plain `manage.py migrate --run-syncdb` cannot do this. Most apps still have no
migrations, and PostgreSQL -- unlike SQLite -- insists that a foreign key's
target table already exist when the constraint is created. That leaves `migrate`
with no workable order of its own:

  * its syncdb phase runs FIRST, but 24 columns in the apps without migrations
    reference auth_user, which the auth migrations haven't created yet;
  * running the migrations first fails just as fast, because
    forums.0001_initial references oembed_oembed, which the syncdb phase owns;
  * and elsewhere's post_migrate hook queries its own tables after every migrate
    call, including the ones that run before those tables exist.

None of it is circular, though -- oembed has no foreign keys of its own -- so
splitting the work into ordered phases is enough:

  A. detach elsewhere's post_migrate hook (its tables don't exist yet)
  B. migrate auth                  -> contenttypes + auth
  C. migrate oembed --run-syncdb   -> the tables forums.0001_initial needs
  D. migrate                       -> django's own apps + the ones with migrations
  E. migrate --run-syncdb          -> everything else
  F. reattach the hook and seed through it

Usage (from inside the web container, against an empty database):

    DB_ENGINE=postgresql python tools/create_pg_schema.py

The script becomes unnecessary the moment every app has migrations: a single
`migrate` will then order the work correctly on its own.
"""
import os
import sys

import django

# Run from anywhere: the project package lives one level up from tools/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.docker')
django.setup()

from django.core.management import call_command
from django.db.models.signals import post_migrate

import elsewhere.management


def phase(label):
    print('\n=== {} '.format(label) + '=' * max(0, 60 - len(label)))


phase('A. detach elsewhere post_migrate hook')
post_migrate.disconnect(elsewhere.management.fill_db)

phase('B. migrate auth')
call_command('migrate', 'auth', verbosity=1)

phase('C. migrate oembed --run-syncdb')
call_command('migrate', 'oembed', run_syncdb=True, verbosity=1)

phase('D. migrate (apps with migrations)')
call_command('migrate', verbosity=1)

phase('E. migrate --run-syncdb (apps without migrations)')
call_command('migrate', run_syncdb=True, verbosity=1)

phase('F. reattach hook and seed through it')
post_migrate.connect(elsewhere.management.fill_db)
elsewhere.management.fill_db()
print('DONE')
