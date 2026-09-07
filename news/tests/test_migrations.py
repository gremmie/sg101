"""
Tests for what the tagging retirement removes.

**These build the rows the migration is supposed to delete, then run it.** The
obvious test -- assert a migrated database has no tagging tables -- cannot fail:
once the app leaves INSTALLED_APPS its tables are never created in a fresh
database, so the assertion holds whether or not the migration does anything at
all. What is worth pinning is that a database which *does* carry them comes out
clean, which is the only database this migration will ever meet in production.
"""
import importlib

from django.apps import apps as global_apps
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase

drop = importlib.import_module('news.migrations.0011_drop_tagging_tables')


def table_names():
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def column_names(table):
    with connection.cursor() as cursor:
        return {c.name for c in connection.introspection.get_table_description(
            cursor, table)}


def run_drop():
    with connection.schema_editor() as editor:
        drop.drop_tagging(global_apps, editor)


class DropTaggingTests(TestCase):
    """Each test creates what it expects the migration to remove."""

    def make_tables(self):
        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE tagging_tag (id serial PRIMARY KEY, '
                           'name varchar(50) NOT NULL)')
            cursor.execute('CREATE TABLE tagging_taggeditem ('
                           'id serial PRIMARY KEY, '
                           'tag_id integer NOT NULL REFERENCES tagging_tag(id))')

    def make_content_types(self):
        tag = ContentType.objects.create(app_label='tagging', model='tag')
        item = ContentType.objects.create(app_label='tagging', model='taggeditem')
        for content_type in (tag, item):
            Permission.objects.create(content_type=content_type,
                                      codename='add_%s' % content_type.model,
                                      name='Can add %s' % content_type.model)
        return tag, item

    def test_the_tables_are_dropped(self):
        self.make_tables()
        self.assertIn('tagging_tag', table_names())

        run_drop()

        self.assertNotIn('tagging_tag', table_names())
        self.assertNotIn('tagging_taggeditem', table_names())

    def test_the_migration_history_is_cleared(self):
        """A leftover row makes `migrate` on a freshly converted snapshot find
        applied migrations for an app that is not installed."""
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO django_migrations (app, name, applied) "
                           "VALUES ('tagging', '0001_initial', now())")

        run_drop()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM django_migrations WHERE app = 'tagging'")
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_the_content_types_and_their_permissions_go(self):
        """Left behind, these offer "tagging | tag | Can add tag" in the admin's
        permission picker forever."""
        self.make_content_types()
        self.assertEqual(
            Permission.objects.filter(content_type__app_label='tagging').count(), 2)

        run_drop()

        self.assertFalse(ContentType.objects.filter(app_label='tagging').exists())
        self.assertFalse(
            Permission.objects.filter(content_type__app_label='tagging').exists())

    def test_a_granted_permission_does_not_block_the_delete(self):
        """`on_delete=CASCADE` is enforced by Django's deletion collector in
        Python and never reaches the DDL, so the database's own foreign keys are
        NO ACTION and raw SQL gets no cascade. Nothing holds these permissions
        today, but the migration must not depend on that staying true.
        """
        tag, _ = self.make_content_types()
        user = User.objects.create_user('editor', '', 'pw')
        user.user_permissions.add(
            Permission.objects.get(content_type=tag, codename='add_tag'))

        run_drop()

        self.assertFalse(ContentType.objects.filter(app_label='tagging').exists())
        self.assertEqual(user.user_permissions.count(), 0)

    def test_it_is_a_no_op_on_a_database_that_never_had_the_app(self):
        """Every fresh database takes this path, including each test database
        and the one built at deploy time."""
        run_drop()
        run_drop()

        self.assertNotIn('tagging_tag', table_names())


class LegacyColumnTests(TestCase):

    def test_the_legacy_tag_column_is_gone_from_both_tables(self):
        """Read the database, not the model: the field was removed from
        models.py in the same change, so `_meta` would say it is gone whether or
        not the migration ever dropped the column."""
        for table in ('news_story', 'news_pendingstory'):
            columns = column_names(table)
            self.assertNotIn('tags_legacy', columns)
            self.assertIn('tags', columns)


class AppRemovalTests(TestCase):

    def test_the_app_is_not_installed(self):
        self.assertFalse(global_apps.is_installed('tagging'))
