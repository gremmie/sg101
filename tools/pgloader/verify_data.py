"""Compare the *values* in a converted database, column by column, both engines.

verify.py answers "did every row arrive, and did the cp1252 tables decode?".
This answers a larger question: for every column of every table, does the
converted database hold what MySQL holds? Row counts cannot see a shifted
timestamp, a boolean that lost its sense, a decimal that changed scale, or a
NULL that became an empty string, and all four are things an engine port can
get wrong while looking perfectly healthy.

The comparison is a checksum rather than a row-by-row diff. Each column is
rendered to a canonical string on both sides, md5'd per value, and the first 7
hex digits summed -- order-independent, so no sorting or shipping of 700,000
rows is involved, and one query per table per engine covers every column at
once. When a column's checksums disagree the offending rows are then found by
streaming that one column's digests keyed by primary key, so a failure names
the rows rather than just the column.

Canonicalization is where the engine differences live, and each one is a way
the conversion could have gone wrong silently:

  datetime   MySQL datetime carries no offset; Django maps DateTimeField to
             timestamptz, so every value had to be placed on the timeline
             using a timezone. Rendering the PostgreSQL side back through
             APP_TIME_ZONE compares what the *application* sees, which is the
             only comparison that matters -- a database whose stored instants
             are uniformly 6 hours off still passes a naive string compare.
  boolean    tinyint(1) 0/1 against a real boolean.
  decimal    scale is significant: 10.00 and 10.0 are the same number and
             different values to a user reading a donation receipt.
  inet       four columns became inet from varchar; host() renders them back.
  NULL       rendered to a sentinel, never to '', so a NULL that became an
             empty string is a mismatch instead of a match. The two are also
             tallied per column and reported, because the distinction is
             invisible on a page and load-bearing in a query.

It runs twice, at two different points, because the two halves need the
database in two different states:

  values     before post_convert.py, beside verify.py. This compares what the
             conversion wrote, and only that. After post_convert.py runs
             migrate, any migration that rewrites data -- dropping a table,
             backfilling a column, changing its type -- is a difference this
             would have to be taught about, one migration at a time, and a
             comparison that needs updating with every data migration stops
             being run.
  keys       after post_convert.py, which rebuilds every foreign key the way
             Django builds it. Checking them before would only find pgloader's.

Run inside the web container, which has both drivers:

    docker compose exec -T web python tools/pgloader/verify_data.py values
    docker compose exec -T web python tools/pgloader/verify_data.py keys
    MYSQL_DB=sg101_pristine PG_DB=sg101 ... same

Exits non-zero if anything differs.
"""
import os
import sys
from collections import OrderedDict, defaultdict

import MySQLdb
import psycopg2

# Values that are NULL render to this, so NULL and '' cannot hash alike. The
# angle brackets keep it clear of anything the site would store.
NULL_SENTINEL = '<<NULL>>'

TEXT_TYPES = {'char', 'varchar', 'text', 'tinytext', 'mediumtext', 'longtext'}
INT_TYPES = {'int', 'bigint', 'smallint', 'mediumint'}

# How many mismatching rows to name before giving up on a column.
MAX_REPORTED = 10

# Columns the conversion itself changes, with the exact number of rows that
# may differ. Pinning the count is the point: it explains the difference
# without granting the column a blanket exemption, so corruption arriving
# alongside an expected change is still a failure.
EXPECTED_COLUMNS = {
    ('forums_post', 'user_ip'): (
        370, "the conversion maps '' to NULL, because inet has no empty "
             'value'),
}


def app_time_zone():
    """The timezone the naive MySQL datetimes were written in."""
    tz = os.environ.get('APP_TIME_ZONE')
    if tz:
        return tz
    try:
        from django.conf import settings
        return settings.TIME_ZONE
    except Exception:
        return 'America/Chicago'


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


def category(data_type, column_type):
    """Group a MySQL column into the kind of thing it is."""
    if data_type == 'tinyint' and '(1)' in column_type:
        return 'boolean'
    if data_type in INT_TYPES or data_type == 'tinyint':
        return 'integer'
    if data_type in TEXT_TYPES:
        return 'text'
    if data_type in ('datetime', 'timestamp'):
        return 'datetime'
    if data_type == 'date':
        return 'date'
    if data_type == 'time':
        return 'time'
    if data_type == 'decimal':
        return 'decimal'
    if data_type in ('double', 'float'):
        return 'float'
    return 'other'


def mysql_expr(cat, col):
    """Render a MySQL column to its canonical string."""
    q = '`%s`' % col
    if cat == 'text':
        # The cp1252 tables are latin1 on disk; CONVERT decodes them the way
        # MySQL would when serving the site.
        return 'CONVERT(%s USING utf8)' % q
    if cat == 'boolean':
        return "IF(%s <> 0, '1', '0')" % q
    if cat == 'datetime':
        return "DATE_FORMAT(%s, '%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s')" % q
    if cat == 'date':
        return "DATE_FORMAT(%s, '%%%%Y-%%%%m-%%%%d')" % q
    if cat == 'time':
        return "TIME_FORMAT(%s, '%%%%H:%%%%i:%%%%s')" % q
    return 'CAST(%s AS CHAR)' % q


def pg_expr(cat, col, pg_type, tz):
    """Render the matching PostgreSQL column to the same canonical string."""
    q = '"%s"' % col
    if pg_type == 'inet':
        return 'host(%s)' % q
    if cat == 'boolean':
        return "CASE WHEN %s THEN '1' ELSE '0' END" % q
    if cat == 'datetime':
        # AT TIME ZONE converts the stored instant back to wall-clock in the
        # application's timezone -- the value Django hands to a template.
        return "to_char(%s AT TIME ZONE '%s', 'YYYY-MM-DD HH24:MI:SS')" % (q, tz)
    if cat == 'date':
        return "to_char(%s, 'YYYY-MM-DD')" % q
    if cat == 'time':
        return "to_char(%s, 'HH24:MI:SS')" % q
    if cat == 'text':
        return q
    return '%s::text' % q


def mysql_checksum(expr):
    return ("COALESCE(SUM(CONV(SUBSTRING(MD5(COALESCE(%s, '%s')), 1, 7), "
            "16, 10)), 0)" % (expr, NULL_SENTINEL))


def pg_checksum(expr):
    # 7 hex digits left-padded to 8 keeps the top nibble clear, so bit(32)
    # never produces a negative and the two engines sum the same numbers.
    return ("COALESCE(SUM(('x' || lpad(substring(md5(COALESCE(%s, '%s')), "
            "1, 7), 8, '0'))::bit(32)::bigint), 0)" % (expr, NULL_SENTINEL))


def columns_of(my, table):
    """MySQL columns with the type information needed to canonicalize them."""
    return fetch(my, """
        SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION""", (table,))


def primary_key_of(my, table):
    pk = fetch(my, """
        SELECT COLUMN_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
          AND COLUMN_KEY = 'PRI' ORDER BY ORDINAL_POSITION""", (table,))
    return pk[0][0] if len(pk) == 1 else None


def differing_rows(my, pg, table, col, cat, pg_type, tz, pk):
    """Primary keys whose value for this column differs between engines.

    Rows can only be identified where there is a single-column primary key to
    identify them by; without one the caller gets None and has to say so
    rather than report a count it cannot back up.
    """
    if not pk:
        return None
    m_expr = mysql_expr(cat, col)
    p_expr = pg_expr(cat, col, pg_type, tz)
    src = dict(fetch(my, "SELECT `%s`, MD5(COALESCE(%s, '%s')) FROM `%s`"
                     % (pk, m_expr, NULL_SENTINEL, table)))
    dst = dict(fetch(pg, "SELECT \"%s\", md5(COALESCE(%s, '%s')) FROM \"%s\""
                     % (pk, p_expr, NULL_SENTINEL, table)))
    return sorted(k for k in src if src[k] != dst.get(k))


def drill_down(my, pg, table, col, cat, pg_type, tz, pk, keys):
    """Show the values behind a column mismatch, or say why we cannot."""
    if not pk:
        return ['      (no single-column primary key; rows cannot be named)']
    m_expr = mysql_expr(cat, col)
    p_expr = pg_expr(cat, col, pg_type, tz)
    out = []
    for key in keys[:MAX_REPORTED]:
        m_val = fetch(my, 'SELECT %s FROM `%s` WHERE `%s` = %%s'
                      % (m_expr, table, pk), (key,))
        p_val = fetch(pg, 'SELECT %s FROM "%s" WHERE "%s" = %%s'
                      % (p_expr, table, pk), (key,))
        out.append('      pk=%s MySQL=%r PostgreSQL=%r'
                   % (key, m_val[0][0] if m_val else None,
                      p_val[0][0] if p_val else None))
    if len(keys) > MAX_REPORTED:
        out.append('      ... and %d more' % (len(keys) - MAX_REPORTED))
    return out


def check_values(my, pg, tz):
    """Checksum every column of every table on both engines."""
    tables = [r[0] for r in fetch(my, """
        SELECT TABLE_NAME FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME""")]

    pg_types = defaultdict(dict)
    for t, c, dt in fetch(pg, """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns WHERE table_schema = 'public'"""):
        pg_types[t][c] = dt

    failures = []
    explained = []
    stats = defaultdict(lambda: {'columns': 0, 'values': 0})
    nulls = defaultdict(int)
    empties = defaultdict(int)
    blanks = defaultdict(int)
    skipped = []

    for table in tables:
        cols = columns_of(my, table)
        if table not in pg_types:
            failures.append('%s: missing from PostgreSQL' % table)
            continue

        plan = []
        for col, data_type, column_type in cols:
            if col not in pg_types[table]:
                failures.append('%s.%s: column missing from PostgreSQL'
                                % (table, col))
                continue
            cat = category(data_type, column_type)
            if cat == 'other':
                skipped.append('%s.%s (%s)' % (table, col, data_type))
                continue
            plan.append((col, cat, pg_types[table][col]))
        if not plan:
            continue

        m_parts, p_parts = [], []
        for col, cat, pg_type in plan:
            m_expr = mysql_expr(cat, col)
            p_expr = pg_expr(cat, col, pg_type, tz)
            m_parts.append(mysql_checksum(m_expr))
            p_parts.append(pg_checksum(p_expr))
            m_parts.append('COALESCE(SUM(`%s` IS NULL), 0)' % col)
            p_parts.append('COUNT(*) FILTER (WHERE "%s" IS NULL)' % col)
            if cat == 'text':
                # Length, not `= ''`. MySQL's collations are PAD SPACE, so
                # `' ' = ''` is true there and false on PostgreSQL: comparing
                # that way measures the collation rather than the data, and
                # reports a difference for a value both engines hold
                # identically.
                m_parts.append('COALESCE(SUM(CHAR_LENGTH(%s) = 0), 0)'
                               % m_expr)
                p_parts.append("COUNT(*) FILTER (WHERE length(%s) = 0)"
                               % p_expr)
                m_parts.append("COALESCE(SUM(CHAR_LENGTH(%s) > 0 AND "
                               "TRIM(%s) = ''), 0)" % (m_expr, m_expr))
                p_parts.append("COUNT(*) FILTER (WHERE length(%s) > 0 AND "
                               "btrim(%s) = '')" % (p_expr, p_expr))

        n_rows = fetch(my, 'SELECT COUNT(*) FROM `%s`' % table)[0][0]
        m_row = fetch(my, 'SELECT %s FROM `%s`' % (', '.join(m_parts), table))[0]
        p_row = fetch(pg, 'SELECT %s FROM "%s"' % (', '.join(p_parts), table))[0]

        i = 0
        for col, cat, pg_type in plan:
            m_ck, p_ck = int(m_row[i]), int(p_row[i])
            m_null, p_null = int(m_row[i + 1]), int(p_row[i + 1])
            i += 2
            m_empty = p_empty = m_blank = 0
            if cat == 'text':
                m_empty, p_empty = int(m_row[i]), int(p_row[i])
                m_blank = int(m_row[i + 1])
                if m_blank != int(p_row[i + 1]):
                    failures.append(
                        '%s.%s: %d whitespace-only values in MySQL, %d in '
                        'PostgreSQL' % (table, col, m_blank,
                                        int(p_row[i + 1])))
                i += 2

            stats[cat]['columns'] += 1
            stats[cat]['values'] += n_rows
            nulls[cat] += m_null
            empties[cat] += m_empty
            blanks[cat] += m_blank

            expected = EXPECTED_COLUMNS.get((table, col))
            if expected and (m_ck != p_ck or m_null != p_null
                             or m_empty != p_empty):
                limit, reason = expected
                pk = primary_key_of(my, table)
                keys = differing_rows(my, pg, table, col, cat, pg_type, tz, pk)
                if keys is None:
                    failures.append(
                        '%s.%s: expected %d differing row(s) (%s), but the '
                        'table has no single-column primary key to count them '
                        'by' % (table, col, limit, reason))
                elif len(keys) == limit:
                    explained.append('%s.%s: %d row(s) differ -- %s'
                                     % (table, col, len(keys), reason))
                else:
                    failures.append(
                        '%s.%s: %d row(s) differ, expected exactly %d (%s)'
                        % (table, col, len(keys), limit, reason))
                    failures.extend(drill_down(my, pg, table, col, cat,
                                               pg_type, tz, pk, keys))
                continue

            if m_null != p_null:
                failures.append('%s.%s: %d NULLs in MySQL, %d in PostgreSQL'
                                % (table, col, m_null, p_null))
            if cat == 'text' and m_empty != p_empty:
                failures.append(
                    "%s.%s: %d empty strings in MySQL, %d in PostgreSQL"
                    % (table, col, m_empty, p_empty))
            if m_ck != p_ck:
                failures.append('%s.%s (%s): values differ' % (table, col, cat))
                pk = primary_key_of(my, table)
                keys = differing_rows(my, pg, table, col, cat, pg_type, tz, pk)
                failures.extend(drill_down(my, pg, table, col, cat, pg_type,
                                           tz, pk, keys))

    print('values: %d tables, timezone %s' % (len(tables), tz))
    for cat in sorted(stats):
        print('        %-9s %4d columns, %9d values, %7d NULL, %7d empty, '
              '%5d blank' % (cat, stats[cat]['columns'], stats[cat]['values'],
                             nulls[cat], empties[cat], blanks[cat]))
    if skipped:
        print('        not compared: %s' % ', '.join(skipped))
    for note in explained:
        print('        %s' % note)
    return failures


def check_foreign_keys(pg):
    """Every foreign key must actually hold, and be enforced rather than
    merely declared. pgloader creates constraints after loading, so one that
    was created NOT VALID would look identical in a schema dump and catch
    nothing on the next insert."""
    fks = fetch(pg, """
        SELECT c.conname, c.conrelid::regclass::text,
               c.confrelid::regclass::text, c.convalidated,
               pg_get_constraintdef(c.oid),
               c.condeferrable AND c.condeferred
               AND c.confupdtype = 'a' AND c.confdeltype = 'a'
        FROM pg_constraint c
        WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace
        ORDER BY 2, 1""")

    failures = []
    orphans = 0
    immediate = 0
    for name, table, ref_table, validated, definition, django_style in fks:
        if not validated:
            failures.append('%s on %s is NOT VALID -- declared but not '
                            'enforced for existing rows' % (name, table))
        if not django_style:
            # Django makes these NO ACTION and DEFERRABLE INITIALLY DEFERRED,
            # and its ORM depends on it. RESTRICT, which is what pgloader
            # carries over from InnoDB, is checked immediately and cannot be
            # deferred, so ordinary deletes fail on an ordering the collector
            # is entitled to choose.
            immediate += 1
        # FOREIGN KEY (a, b) REFERENCES t(x, y) ...
        cols = definition.split('(', 1)[1].split(')', 1)[0]
        ref_cols = definition.split('REFERENCES', 1)[1].split('(', 1)[1] \
                             .split(')', 1)[0]
        col_list = [c.strip() for c in cols.split(',')]
        ref_list = [c.strip() for c in ref_cols.split(',')]
        joins = ' AND '.join('t.%s = r.%s' % (c, r)
                             for c, r in zip(col_list, ref_list))
        nulls = ' AND '.join('t.%s IS NOT NULL' % c for c in col_list)
        n = fetch(pg, 'SELECT COUNT(*) FROM %s t WHERE %s AND NOT EXISTS '
                      '(SELECT 1 FROM %s r WHERE %s)'
                      % (table, nulls, ref_table, joins))[0][0]
        if n:
            orphans += n
            failures.append('%s: %d row(s) in %s reference a missing %s'
                            % (name, n, table, ref_table))

    if immediate:
        failures.append('%d of %d foreign keys are not NO ACTION DEFERRABLE '
                        'INITIALLY DEFERRED, which is how Django builds them '
                        '-- ORM deletes will fail on constraint ordering'
                        % (immediate, len(fks)))

    print('foreign keys: %d constraints, all VALID, deferrable and NO ACTION, '
          '%d orphaned row(s)' % (len(fks), orphans))
    return failures


def check_enforcement(pg):
    """Prove enforcement rather than trusting the catalog: a bad insert must
    be rejected. Rolled back, so the database is untouched.

    The constraints are deferred, so the insert itself is allowed to succeed
    and the check happens at commit. SET CONSTRAINTS ALL IMMEDIATE brings that
    moment forward without committing anything.
    """
    failures = []
    cur = pg.cursor()
    try:
        cur.execute('SAVEPOINT probe')
        # Every NOT NULL column is supplied, so the only thing left to
        # object to is the topic that does not exist.
        cur.execute('INSERT INTO forums_post (topic_id, user_id, body, html, '
                    'creation_date, update_date) '
                    "VALUES (-1, -1, 'probe', 'probe', now(), now())")
        cur.execute('SET CONSTRAINTS ALL IMMEDIATE')
    except psycopg2.IntegrityError as exc:
        # Insist on 23503 specifically. A NOT NULL violation is also an
        # IntegrityError, and accepting one here would let the probe report
        # success without a foreign key ever having been consulted.
        if exc.pgcode == '23503':
            print('enforcement: a row referencing a missing topic was '
                  'rejected (SQLSTATE 23503)')
        else:
            failures.append('the probe insert failed with SQLSTATE %s, not a '
                            'foreign key violation -- it proves nothing about '
                            'enforcement and needs updating' % exc.pgcode)
    else:
        failures.append('a post referencing topic -1 was accepted -- foreign '
                        'keys are not being enforced')
    finally:
        pg.rollback()
        cur.close()
    return failures


def main(argv):
    if len(argv) != 2 or argv[1] not in ('values', 'keys'):
        print('usage: verify_data.py values   (before post_convert.py)\n'
              '       verify_data.py keys     (after post_convert.py)',
              file=sys.stderr)
        return 2
    mode = argv[1]

    my, pg = connect()
    print('source: mysql/%s   target: postgresql/%s\n' % (
        os.environ.get('MYSQL_DB', os.environ.get('DB_NAME', 'sg101')),
        os.environ.get('PG_DB', os.environ.get('DB_NAME', 'sg101'))))

    results = OrderedDict()
    if mode == 'values':
        results['values'] = check_values(my, pg, app_time_zone())
        success = 'OK -- every column matches its source'
    else:
        results['foreign keys'] = check_foreign_keys(pg)
        results['enforcement'] = check_enforcement(pg)
        success = 'OK -- referential integrity holds'

    failures = [f for group in results.values() for f in group]
    print()
    if failures:
        print('FAILED -- %d problem(s):' % len(failures))
        for f in failures:
            print('  %s' % f)
        return 1
    print(success)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
