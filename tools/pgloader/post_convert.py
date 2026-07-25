"""Bring a freshly converted database up to the current migration state.

pgloader copies django_migrations across as it was in MySQL, so the converted
database arrives at whatever migration state production was on -- for the July
2026 snapshot, Django 1.9 era. This applies everything since.

Two things make it more than a plain `migrate`:

1.  Twenty-one apps had their initial migrations backfilled after that
    snapshot was taken. Their tables already exist, so the initials must be
    faked rather than applied, hence --fake-initial.

2.  forums/0001_initial has declared a dependency on ('oembed', '__first__')
    since 2015. That was inert while oembed had no migrations; now that it has
    one, Django's consistency check sees forums.0001 applied without
    oembed.0001 and refuses *every* migrate command with
    InconsistentMigrationHistory. --fake cannot get past it, because the check
    runs first. The one-time unlock is to record oembed's initial directly.
    Safe here: oembed's tables came from the conversion and were verified
    against its models during the backfill.

Run inside the web container, pointed at the converted database:

    docker compose exec -T -e DB_ENGINE=postgresql web \
        python tools/pgloader/post_convert.py
"""
import os
import sys

# Run from anywhere: the settings package lives at the repo root, which is not
# on sys.path when a script two directories down is executed directly.
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')))

import django


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.docker')
    django.setup()

    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder

    print('database: %s on %s' % (connection.settings_dict['NAME'],
                                  connection.vendor))

    recorder = MigrationRecorder(connection)
    applied = recorder.applied_migrations()
    has_forums = ('forums', '0001_initial') in applied
    has_oembed = ('oembed', '0001_initial') in applied

    if has_forums and not has_oembed:
        recorder.record_applied('oembed', '0001_initial')
        print('recorded oembed.0001_initial to clear the forums dependency')
    else:
        print('oembed/forums history already consistent, nothing to unlock')

    call_command('migrate', fake_initial=True, verbosity=1)

    # Faking the initials means Django never creates its prefix-matching
    # indexes, and pgloader has nothing in MySQL to copy them from.
    sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'pattern_ops_indexes.sql')
    with open(sql_path) as fp:
        sql = fp.read()
    with connection.cursor() as cursor:
        cursor.execute(sql)
    created = sum(1 for line in sql.splitlines()
                  if line.startswith('CREATE INDEX'))
    print('applied %d prefix-matching index definitions' % created)
    return 0


if __name__ == '__main__':
    sys.exit(main())
