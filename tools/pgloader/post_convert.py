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
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.dev')
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

    print('rebuilt %d foreign key(s) with Django\'s semantics'
          % align_foreign_keys(connection))
    print('added %d missing check constraint(s)'
          % add_check_constraints(connection))
    print('dropped %d column default(s) Django does not set'
          % drop_column_defaults(connection))
    return 0


def add_check_constraints(connection):
    """Add the CHECK constraints Django's field types imply.

    PositiveIntegerField and PositiveSmallIntegerField are ordinary integer
    columns on PostgreSQL plus a CHECK that they are not negative. MySQL
    expressed the same idea as UNSIGNED, which has no equivalent for pgloader
    to carry across, so the converted database enforces nothing and a negative
    value would be accepted where the model promises otherwise.

    The constraints are asked of Django rather than listed here, so a field
    that changes type -- or a new one -- is covered without this being
    updated, and the names match what a migration would have produced.
    """
    from django.apps import apps

    added = 0
    with connection.schema_editor(atomic=False) as editor:
        for model in apps.get_models():
            table = model._meta.db_table
            with connection.cursor() as cursor:
                existing = connection.introspection.get_constraints(cursor,
                                                                    table)
            checked = {tuple(info['columns'])
                       for info in existing.values() if info.get('check')}
            for field in model._meta.local_fields:
                check = field.db_parameters(connection=connection)['check']
                if not check or (field.column,) in checked:
                    continue
                name = editor._create_index_name(table, [field.column],
                                                 suffix='_check')
                editor.execute(editor._create_check_sql(model, name, check))
                added += 1
    return added


def drop_column_defaults(connection):
    """Remove database-level defaults pgloader carried over from MySQL.

    Django applies field defaults in Python and deliberately leaves none in
    the database -- its schema editor drops the default as soon as it has
    used it to backfill a column. Two columns arrive from MySQL still
    carrying DEFAULT 0, which nothing reads while Django always supplies a
    value, but which makes the converted schema disagree with a migrated one
    for no reason.

    Sequence defaults are left alone: those are what makes a column serial.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND column_default IS NOT NULL
              AND column_default NOT LIKE 'nextval%'
            ORDER BY 1, 2""")
        targets = cursor.fetchall()
        for table, column in targets:
            cursor.execute('ALTER TABLE "%s" ALTER COLUMN "%s" DROP DEFAULT'
                           % (table, column))
    return len(targets)


def align_foreign_keys(connection):
    """Rebuild the foreign keys the way Django's schema editor makes them.

    Django creates every foreign key on PostgreSQL as a plain NO ACTION
    constraint that is DEFERRABLE INITIALLY DEFERRED, and its ORM depends on
    that combination. Cascades are performed in Python by the deletion
    collector, which removes rows in whatever order suits it and leaves the
    database to confirm consistency once, at commit.

    pgloader carries MySQL's InnoDB semantics across instead, and writes every
    constraint ON UPDATE RESTRICT ON DELETE RESTRICT. RESTRICT is not the same
    as NO ACTION: it is checked immediately and cannot be deferred, so the
    collector's ordering starts to matter and operations that work against a
    migrated database fail against a converted one. Deleting a forum topic is
    enough to show it -- the topic's own last_post points at a post being
    removed in the same transaction, and the delete aborts.

    The action is part of the constraint, so this drops and recreates each one
    rather than altering it. Recreating revalidates against the existing rows,
    which is the check worth having anyway.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT conrelid::regclass::text, conname,
                   pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE contype = 'f' AND connamespace = 'public'::regnamespace
              AND (confupdtype <> 'a' OR confdeltype <> 'a'
                   OR NOT condeferrable OR NOT condeferred)
            ORDER BY 1, 2""")
        targets = cursor.fetchall()
        for table, name, definition in targets:
            # FOREIGN KEY (a) REFERENCES t(b) [ON ...] [DEFERRABLE ...]
            keep = definition.split(' ON UPDATE')[0].split(' ON DELETE')[0] \
                             .split(' DEFERRABLE')[0].strip()
            cursor.execute('ALTER TABLE %s DROP CONSTRAINT "%s"'
                           % (table, name))
            cursor.execute('ALTER TABLE %s ADD CONSTRAINT "%s" %s '
                           'DEFERRABLE INITIALLY DEFERRED'
                           % (table, name, keep))
    return len(targets)


if __name__ == '__main__':
    sys.exit(main())
