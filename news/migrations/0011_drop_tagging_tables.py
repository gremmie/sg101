"""Drop what the tagging app left behind.

The site has been reading tags from the array column since the previous two
migrations; this removes the tables that fed it, the string column they were
kept in step with, and the migration history and content types Django created
for models that no longer exist.

Everything here is guarded, because the same migration has to be correct on a
database that has all of it and on one built from scratch that never had any of
it -- which is the case at deploy time, and the case every test database takes.

"""
from django.db import migrations


def drop_tagging(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # The join table first: it carries the foreign key into tagging_tag.
        cursor.execute('DROP TABLE IF EXISTS tagging_taggeditem')
        cursor.execute('DROP TABLE IF EXISTS tagging_tag')

        # Without this, `migrate` against a freshly converted production
        # snapshot finds three applied migrations for an app that is not
        # installed and cannot reconcile them against the tree.
        cursor.execute("DELETE FROM django_migrations WHERE app = 'tagging'")

        # Two content types and the eight permissions hanging off them. Left in
        # place they would offer "tagging | tag | Can add tag" in the admin's
        # permission picker forever, naming a model that no longer exists.
        #
        # The rows have to come out in dependency order by hand. Django's
        # on_delete=CASCADE is enforced by its deletion collector in Python and
        # never reaches the DDL, so the database's own foreign keys are plain
        # NO ACTION and raw SQL gets no cascade at all.
        cursor.execute("""
            DELETE FROM auth_group_permissions WHERE permission_id IN (
                SELECT p.id FROM auth_permission p
                JOIN django_content_type ct ON ct.id = p.content_type_id
                WHERE ct.app_label = 'tagging')
        """)
        cursor.execute("""
            DELETE FROM auth_user_user_permissions WHERE permission_id IN (
                SELECT p.id FROM auth_permission p
                JOIN django_content_type ct ON ct.id = p.content_type_id
                WHERE ct.app_label = 'tagging')
        """)
        cursor.execute("""
            DELETE FROM auth_permission WHERE content_type_id IN (
                SELECT id FROM django_content_type WHERE app_label = 'tagging')
        """)
        cursor.execute("DELETE FROM django_content_type WHERE app_label = 'tagging'")


def unsupported(apps, schema_editor):
    raise RuntimeError(
        'Dropping the tagging tables cannot be undone: the tables can be '
        'recreated but their contents cannot. Restore a snapshot, or reverse '
        'news.0010 first while the tables still exist.')


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0010_backfill_story_tags'),
    ]

    operations = [
        migrations.RemoveField(model_name='pendingstory', name='tags_legacy'),
        migrations.RemoveField(model_name='story', name='tags_legacy'),
        migrations.RunPython(drop_tagging, unsupported),
    ]
