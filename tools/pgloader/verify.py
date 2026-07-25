"""Verify a pgloader conversion against its MySQL source.

Checks three things the conversion can get wrong silently:

  counts    every table's exact row count, MySQL vs PostgreSQL. information_
            schema.TABLE_ROWS is an estimate for InnoDB and is not used.
  encoding  the eight latin1 tables, value by value. MySQL converts latin1 to
            utf8 on the way out, PostgreSQL is already UTF-8, so comparing the
            md5 of both gives a byte-exact answer without shipping the text
            around. A table with no non-ASCII text to compare is reported as
            such rather than passing quietly.
  sequences every sequence sits at or above MAX(pk), so the next insert cannot
            collide.

Run inside the web container, which has both drivers:

    docker compose exec -T web python tools/pgloader/verify.py
    MYSQL_DB=sg101_pristine PG_DB=sg101 ... same

Exits non-zero if anything fails, so it can gate the conversion.
"""
import os
import sys
from collections import OrderedDict

import MySQLdb
import psycopg2

LATIN1_TABLES = [
    'bandmap_bandentry',
    'contests_contest',
    'contests_contest_contestants',
    'contests_contest_winners',
    'countdown_event',
    'django_migrations',
    'messages_flag',
    'user_photos_photo',
]

TEXT_TYPES = {'char', 'varchar', 'text', 'tinytext', 'mediumtext', 'longtext'}

# post_convert.py legitimately adds rows to these: migrate records what it
# applies, and post_migrate creates permissions for every model added since
# the snapshot's Django version. Run this before post_convert.py for a
# like-for-like comparison; run it after and these two will differ, which is
# reported rather than failed.
GROWS_AFTER_MIGRATE = {'auth_permission', 'django_migrations'}


def connect():
    my = MySQLdb.connect(
        host=os.environ.get('MYSQL_HOST', 'db'),
        user=os.environ.get('DB_USER', 'sg101'),
        passwd=os.environ.get('DB_PASSWORD', 'sg101'),
        db=os.environ.get('MYSQL_DB', os.environ.get('DB_NAME', 'sg101')),
        charset='utf8')
    pg = psycopg2.connect(
        host=os.environ.get('PG_HOST', 'postgres'),
        user=os.environ.get('DB_USER', 'sg101'),
        password=os.environ.get('DB_PASSWORD', 'sg101'),
        dbname=os.environ.get('PG_DB', os.environ.get('DB_NAME', 'sg101')))
    return my, pg


def fetch(conn, sql, args=None):
    cur = conn.cursor()
    cur.execute(sql, args or ())
    rows = cur.fetchall()
    cur.close()
    return rows


def check_counts(my, pg):
    """Exact row counts for every table present in MySQL."""
    tables = [r[0] for r in fetch(my, """
        SELECT TABLE_NAME FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME""")]

    pg_tables = {r[0] for r in fetch(pg, """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'""")}

    failures = []
    total_my = total_pg = 0
    for table in tables:
        if table not in pg_tables:
            failures.append('%s: missing from PostgreSQL' % table)
            continue
        n_my = fetch(my, 'SELECT COUNT(*) FROM `%s`' % table)[0][0]
        n_pg = fetch(pg, 'SELECT COUNT(*) FROM "%s"' % table)[0][0]
        total_my += n_my
        total_pg += n_pg
        if n_my == n_pg:
            continue
        if table in GROWS_AFTER_MIGRATE and n_pg > n_my:
            print('        %s: %d -> %d (expected; migrations have been '
                  'applied)' % (table, n_my, n_pg))
            continue
        failures.append('%s: MySQL %d != PostgreSQL %d' % (table, n_my, n_pg))

    extra = pg_tables - set(tables)
    print('counts: %d tables, %d rows in MySQL, %d in PostgreSQL' % (
        len(tables), total_my, total_pg))
    if extra:
        print('        %d table(s) only in PostgreSQL: %s' % (
            len(extra), ', '.join(sorted(extra))))
    return failures


def check_encoding(my, pg):
    """Compare every text value in the latin1 tables, md5 against md5."""
    failures = []
    for table in LATIN1_TABLES:
        cols = [r[0] for r in fetch(my, """
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
              AND DATA_TYPE IN ('char','varchar','text','tinytext',
                                'mediumtext','longtext')
            ORDER BY ORDINAL_POSITION""", (table,))]
        pk = fetch(my, """
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
              AND COLUMN_KEY = 'PRI' ORDER BY ORDINAL_POSITION""", (table,))
        if not cols or not pk:
            print('encoding: %-30s skipped (no text columns or no primary key)'
                  % table)
            continue
        pk = pk[0][0]

        compared = non_ascii = 0
        for col in cols:
            # CONVERT(... USING utf8) makes MySQL decode the latin1 bytes, so
            # both sides are hashing the same UTF-8 text.
            src = dict(fetch(my,
                'SELECT `%s`, MD5(CONVERT(`%s` USING utf8)) FROM `%s` '
                'WHERE `%s` IS NOT NULL' % (pk, col, table, col)))
            dst = dict(fetch(pg,
                'SELECT "%s", md5("%s") FROM "%s" WHERE "%s" IS NOT NULL'
                % (pk, col, table, col)))
            n_high = fetch(my,
                'SELECT COUNT(*) FROM `%s` WHERE `%s` REGEXP %s'
                % (table, col, "'[^\\x00-\\x7F]'"))[0][0]
            non_ascii += n_high
            for key, digest in src.items():
                compared += 1
                if dst.get(key) != digest:
                    failures.append('%s.%s pk=%s: md5 differs (MySQL %s, '
                                    'PostgreSQL %s)' % (table, col, key,
                                                        digest, dst.get(key)))
        note = ('%d value(s) contain non-ASCII' % non_ascii if non_ascii
                else 'NO non-ASCII text present -- nothing to compare')
        print('encoding: %-30s %6d values compared, %s' % (
            table, compared, note))
    return failures


def check_sequences(pg):
    """Every sequence must be past the largest value already in its column."""
    seqs = fetch(pg, """
        SELECT c.relname, s.seqrelid::regclass::text
        FROM pg_class c JOIN pg_sequence s ON s.seqrelid = c.oid
        WHERE c.relkind = 'S'""")
    failures = []
    checked = 0
    for name, _ in seqs:
        owner = fetch(pg, """
            SELECT d.refobjid::regclass::text, a.attname
            FROM pg_depend d
            JOIN pg_attribute a ON a.attrelid = d.refobjid
                               AND a.attnum = d.refobjsubid
            WHERE d.objid = %s::regclass AND d.deptype = 'a'""", (name,))
        if not owner:
            continue
        table, column = owner[0]
        checked += 1
        last = fetch(pg, "SELECT last_value FROM %s" % name)[0][0]
        biggest = fetch(pg, 'SELECT COALESCE(MAX("%s"), 0) FROM %s'
                        % (column, table))[0][0]
        if last < biggest:
            failures.append('%s: last_value %d < MAX(%s.%s) %d -- next insert '
                            'would collide' % (name, last, table, column,
                                               biggest))
    print('sequences: %d checked, all at or past MAX(pk)' % checked
          if not failures else 'sequences: %d checked' % checked)
    return failures


def main():
    my, pg = connect()
    print('source: mysql/%s   target: postgresql/%s\n' % (
        os.environ.get('MYSQL_DB', os.environ.get('DB_NAME', 'sg101')),
        os.environ.get('PG_DB', os.environ.get('DB_NAME', 'sg101'))))

    results = OrderedDict()
    results['counts'] = check_counts(my, pg)
    print()
    results['encoding'] = check_encoding(my, pg)
    print()
    results['sequences'] = check_sequences(pg)

    failures = [f for group in results.values() for f in group]
    print()
    if failures:
        print('FAILED -- %d problem(s):' % len(failures))
        for f in failures:
            print('  %s' % f)
        return 1
    print('OK -- counts, encoding and sequences all verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
