"""Fill the new tag arrays from the tagging join table.

The join table is the source of truth, not the old string column: they disagree
on two stories, where MySQL's accent-insensitive index on the tag name matched a
later accented submission to an ASCII tag that already existed. The join table
is what every page renders, so taking it changes nothing a reader can see.

**The tagging tables are addressed by name, in SQL, on purpose.** Going through
`apps.get_model('tagging', ...)` or declaring a dependency on that app's
migrations would strand this file the moment the app is deleted -- a LookupError
and a NodeNotFoundError respectively. Addressing the tables directly means this
migration keeps working, and keeps reversing, after the app is gone.

"""
from django.db import migrations


TAGGING_TABLES = ('tagging_tag', 'tagging_taggeditem')


def _tagging_tables_present(connection):
    existing = set(connection.introspection.table_names())
    return set(TAGGING_TABLES) <= existing


def _content_type_ids(cursor):
    """Content type ids for the two tagged models, by name rather than by the
    hardcoded ids this database happens to have."""
    cursor.execute("""
        SELECT model, id FROM django_content_type
        WHERE app_label = 'news' AND model IN ('story', 'pendingstory')
    """)
    return dict(cursor.fetchall())


def backfill(apps, schema_editor):
    connection = schema_editor.connection
    if not _tagging_tables_present(connection):
        # A database built from scratch never had them, and there is nothing to
        # copy. This is the path a fresh test database takes.
        return

    with connection.cursor() as cursor:
        content_types = _content_type_ids(cursor)
        for model_name, table in (('story', 'news_story'),
                                  ('pendingstory', 'news_pendingstory')):
            content_type_id = content_types.get(model_name)
            if content_type_id is None:
                continue
            cursor.execute("""
                UPDATE {table} s SET tags = COALESCE((
                    SELECT array_agg(t.name ORDER BY t.name)
                    FROM tagging_taggeditem ti
                    JOIN tagging_tag t ON t.id = ti.tag_id
                    WHERE ti.content_type_id = %s AND ti.object_id = s.id
                ), '{{}}')
            """.format(table=table), [content_type_id])


def rebuild_join_table(apps, schema_editor):
    """Put the tags back where they came from.

    This does not restore the 630 rows that pointed at stories and pending
    stories which no longer exist -- 616 of them left behind by story approval,
    which deletes the pending story without deleting its tag rows. They had no
    target to be restored to.

    """
    connection = schema_editor.connection
    if not _tagging_tables_present(connection):
        raise RuntimeError(
            'Cannot reverse: %s do not exist. Restore a snapshot instead.'
            % ' and '.join(TAGGING_TABLES))

    with connection.cursor() as cursor:
        content_types = _content_type_ids(cursor)

        cursor.execute("""
            INSERT INTO tagging_tag (name)
            SELECT DISTINCT x.tag FROM (
                SELECT unnest(tags) AS tag FROM news_story
                UNION
                SELECT unnest(tags) AS tag FROM news_pendingstory
            ) x
            WHERE NOT EXISTS (SELECT 1 FROM tagging_tag t WHERE t.name = x.tag)
        """)

        for model_name, table in (('story', 'news_story'),
                                  ('pendingstory', 'news_pendingstory')):
            content_type_id = content_types.get(model_name)
            if content_type_id is None:
                continue
            cursor.execute(
                'DELETE FROM tagging_taggeditem WHERE content_type_id = %s',
                [content_type_id])
            cursor.execute("""
                INSERT INTO tagging_taggeditem (tag_id, content_type_id, object_id)
                SELECT t.id, %s, s.id
                FROM {table} s
                CROSS JOIN LATERAL unnest(s.tags) AS tag
                JOIN tagging_tag t ON t.name = tag
            """.format(table=table), [content_type_id])


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0009_story_tags_as_an_array'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(backfill, rebuild_join_table),
    ]
