"""Diff a converted database against one Django's own migrations build.

pgloader converts a MySQL schema faithfully. That is not the same as building
the schema Django would have built, and the gap is where this conversion's
worst problems have lived: every foreign key arrived as RESTRICT, which cannot
be deferred, so deleting a forum topic failed against a converted database
while working against a migrated one. Row counts, column types and a green
test suite all looked perfect throughout, because the test suite builds its
schema from the migrations and never sees the converted one.

So this compares the two schemas directly, across every dimension that
changes behavior:

  columns      name, type, length, precision, nullability
  indexes      the columns and expressions indexed, and uniqueness
  constraints  primary keys, uniqueness, and CHECKs
  foreign keys the referenced table and columns, the ON UPDATE/ON DELETE
               action, and deferrability -- Django needs NO ACTION DEFERRABLE
               INITIALLY DEFERRED and its ORM misbehaves without it
  defaults     Django applies field defaults in Python and leaves none in the
               database
  sequences    that each is owned by its column, so pg_get_serial_sequence
               resolves

Names are deliberately not compared. pgloader's indexes are called things like
idx_393735_username where Django's are forums_topic_last_post_id_ed000e17_fk;
Django resolves them by introspection, so the names differ harmlessly and
comparing them would bury the differences that matter.

Build the reference first -- an empty database with migrate run against it:

    docker compose exec -T postgres psql -U sg101 -d postgres \
        -c 'DROP DATABASE IF EXISTS sg101_reference WITH (FORCE)' \
        -c 'CREATE DATABASE sg101_reference'
    docker compose exec -T -e DB_ENGINE=postgresql -e DB_NAME=sg101_reference \
        web python manage.py migrate

then:

    docker compose exec -T web python tools/pgloader/compare_schema.py

Exits non-zero if the schemas differ in a way that is not accounted for.
"""
import os
import sys
from collections import OrderedDict

import psycopg2

# Tables that exist in the converted database and have no model behind them.
# They come across by decision -- a conversion is not the place to prune -- so
# the reference schema will never contain them.
LEGACY_TABLES = {
    'auth_message',
    'core_anonlastvisit',
    'core_userlastvisit',
    'gcalendar_accesstoken',
    'irc_ircchannel',
    'mailer_message',
    'membermap_mapentry',
}

# Differences that are understood and accepted, as
# (dimension, object) -> reason.
ACCEPTED = {
    ('index', 'forums_topic_subscribers False USING btree (topic_id)'):
        'redundant: served by the leading column of the composite unique '
        'index, which is present',
}


def connect(dbname):
    return psycopg2.connect(
        host=os.environ.get('PG_HOST', 'postgres'),
        user=os.environ.get('DB_USER', 'sg101'),
        password=os.environ.get('DB_PASSWORD', 'sg101'),
        dbname=dbname)


def fetch(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    rows = [' '.join('' if v is None else str(v) for v in row)
            for row in cur.fetchall()]
    cur.close()
    return set(rows)


COLUMNS = """
    SELECT table_name, column_name, data_type,
           coalesce(character_maximum_length::text, '-'),
           coalesce(numeric_precision::text, '-'), is_nullable
    FROM information_schema.columns WHERE table_schema = 'public'"""

INDEXES = """
    SELECT c.relname, i.indisunique,
           substring(pg_get_indexdef(i.indexrelid) from 'USING .*')
    FROM pg_index i JOIN pg_class c ON c.oid = i.indrelid
    WHERE c.relnamespace = 'public'::regnamespace"""

CONSTRAINTS = """
    SELECT conrelid::regclass::text, contype,
           regexp_replace(pg_get_constraintdef(oid), '\\s+', ' ', 'g')
    FROM pg_constraint
    WHERE connamespace = 'public'::regnamespace AND contype IN ('p','u','c')"""

# The action and deferrability are the whole point, so they are part of the
# compared text rather than left to the constraint's name.
FOREIGN_KEYS = """
    SELECT conrelid::regclass::text, confrelid::regclass::text,
           confupdtype, confdeltype, condeferrable, condeferred,
           regexp_replace(pg_get_constraintdef(oid), '\\s+', ' ', 'g')
    FROM pg_constraint
    WHERE connamespace = 'public'::regnamespace AND contype = 'f'"""

DEFAULTS = """
    SELECT table_name, column_name, column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' AND column_default IS NOT NULL
      AND column_default NOT LIKE 'nextval%'"""

UNOWNED_SEQUENCES = """
    SELECT c.relname
    FROM pg_class c
    WHERE c.relkind = 'S' AND c.relnamespace = 'public'::regnamespace
      AND NOT EXISTS (SELECT 1 FROM pg_depend d
                      WHERE d.objid = c.oid AND d.deptype = 'a')"""

DIMENSIONS = OrderedDict([
    ('column', COLUMNS),
    ('index', INDEXES),
    ('constraint', CONSTRAINTS),
    ('foreign key', FOREIGN_KEYS),
    ('default', DEFAULTS),
])


def table_of(row):
    return row.split(' ', 1)[0]


def unique_columns(conn):
    """(table, columns) for every uniqueness the database enforces, however
    it happens to be declared."""
    pairs = set()
    for row in fetch(conn, INDEXES):
        table, unique, definition = row.split(' ', 2)
        if unique == 'True' and '(' in definition:
            cols = definition[definition.index('(') + 1:definition.rindex(')')]
            pairs.add((table, cols.strip()))
    return pairs


def reconcile_uniqueness(missing, converted):
    """Match UNIQUE constraints against equivalent unique indexes.

    PostgreSQL enforces uniqueness with an index either way: Django declares a
    UNIQUE constraint and gets an index underneath, while pgloader creates the
    index directly. The two are indistinguishable to anything inserting a row,
    and Django finds either by introspection, so a constraint that is missing
    only in name is not a difference worth reporting -- but one with no index
    behind it at all certainly is.
    """
    enforced = unique_columns(converted)
    reconciled, remaining = [], []
    for row in missing:
        table, contype, definition = row.split(' ', 2)
        if contype == 'u' and definition.startswith('UNIQUE ('):
            cols = definition[definition.index('(') + 1:definition.rindex(')')]
            if (table, cols.strip()) in enforced:
                reconciled.append(row)
                continue
        remaining.append(row)
    return reconciled, remaining


def main():
    converted_name = os.environ.get('PG_DB', 'sg101')
    reference_name = os.environ.get('REFERENCE_DB', 'sg101_reference')
    converted = connect(converted_name)
    try:
        reference = connect(reference_name)
    except psycopg2.OperationalError as exc:
        print('cannot open the reference database %s: %s' % (reference_name,
                                                             exc))
        print('build it with migrate first -- see this file\'s docstring.')
        return 2

    print('converted: %s   reference: %s\n' % (converted_name, reference_name))

    problems = []
    for label, sql in DIMENSIONS.items():
        # The legacy tables have no model, so the reference cannot contain
        # them and their absence is not a difference.
        ours = {r for r in fetch(converted, sql)
                if table_of(r) not in LEGACY_TABLES}
        theirs = fetch(reference, sql)

        missing = sorted(theirs - ours)
        extra = sorted(ours - theirs)
        accounted = 0

        for row in list(missing):
            if (label, row) in ACCEPTED:
                missing.remove(row)
                accounted += 1

        note = ''
        if label == 'constraint':
            reconciled, missing = reconcile_uniqueness(missing, converted)
            if reconciled:
                note = (', %d UNIQUE enforced by an index instead'
                        % len(reconciled))

        plural = label + ('es' if label.endswith('x') else 's')
        print('%-12s %4d here, %4d in the reference%s%s'
              % (plural, len(ours), len(theirs),
                 ', %d accepted' % accounted if accounted else '', note))
        for row in missing:
            problems.append('%s missing: %s' % (label, row))
        for row in extra:
            problems.append('%s only in the converted database: %s'
                            % (label, row))

    unowned = sorted(fetch(converted, UNOWNED_SEQUENCES))
    print('%-12s %4d unowned' % ('sequences', len(unowned)))
    for seq in unowned:
        problems.append('sequence not owned by its column, so '
                        'pg_get_serial_sequence will not resolve it: %s' % seq)

    print()
    if problems:
        print('DIFFERS -- %d difference(s):' % len(problems))
        for problem in problems:
            print('  %s' % problem)
        return 1
    print('OK -- the converted schema matches one built by the migrations')
    return 0


if __name__ == '__main__':
    sys.exit(main())
