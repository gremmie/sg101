"""Tests for the SearchDocument model and its schema."""

import datetime

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from forums.models import Category
from forums.models import Forum
from forums.models import Topic
from search.models import SearchDocument


class SchemaTestCase(TestCase):
    """
    The GIN index and the unique constraint are the two pieces of the schema
    everything downstream relies on, so they are asserted against the database
    rather than against the model definition.

    """
    def index_definitions(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT indexdef FROM pg_indexes WHERE tablename = %s",
                           [SearchDocument._meta.db_table])
            return [row[0] for row in cursor.fetchall()]

    def test_search_vector_has_a_gin_index(self):
        self.assertTrue(any('USING gin' in definition and
                            'search_vector' in definition
                            for definition in self.index_definitions()))

    def test_source_object_is_unique(self):
        self.assertTrue(any('UNIQUE' in definition and
                            'content_type_id' in definition and
                            'object_id' in definition
                            for definition in self.index_definitions()))


class IndexObjectTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')

    def make_topic(self, name):
        return Topic.objects.create(forum=self.forum, user=self.user, name=name)

    def test_indexing_an_object_creates_one_row(self):
        topic = self.make_topic('Jaguar setup')
        SearchDocument.objects.index_object(topic)
        self.assertEqual(SearchDocument.objects.count(), 1)

    def test_reindexing_updates_in_place(self):
        topic = self.make_topic('Jaguar setup')
        first = SearchDocument.objects.index_object(topic)

        topic.name = 'Jazzmaster setup'
        topic.save()
        second = SearchDocument.objects.index_object(topic)

        self.assertEqual(SearchDocument.objects.count(), 1)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(second.title, 'Jazzmaster setup')

    def test_reindexing_advances_indexed_at(self):
        topic = self.make_topic('Jaguar setup')
        first = SearchDocument.objects.index_object(topic).indexed_at
        second = SearchDocument.objects.index_object(topic).indexed_at
        self.assertGreater(second, first)

    def test_reindexing_rebuilds_the_vector(self):
        topic = self.make_topic('Jaguar setup')
        doc = SearchDocument.objects.index_object(topic)

        topic.name = 'Jazzmaster setup'
        topic.save()
        SearchDocument.objects.index_object(topic)

        vector = SearchDocument.objects.filter(pk=doc.pk).values_list(
                'search_vector', flat=True)[0]
        self.assertIn('jazzmast', vector)
        self.assertNotIn('jaguar', vector)

    def test_distinct_objects_get_distinct_rows(self):
        SearchDocument.objects.index_object(self.make_topic('Jaguar setup'))
        SearchDocument.objects.index_object(self.make_topic('Jazzmaster setup'))
        self.assertEqual(SearchDocument.objects.count(), 2)

    def test_indexed_at_records_when_the_row_was_built(self):
        before = timezone.now()
        doc = SearchDocument.objects.index_object(self.make_topic('Jaguar setup'))
        self.assertGreaterEqual(doc.indexed_at, before)


class StaleWriteTestCase(TestCase):
    """
    Two tasks for one object can run at once, so the older read must lose.

    Editing a profile queues this twice -- auth.User and bio.UserProfile are
    one page but two saves, both mapping to the same document -- and the worker
    runs several processes. Whichever task read the source first has the older
    snapshot, and it must not be allowed to write it over a newer one just by
    finishing last.

    """
    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.topic = Topic.objects.create(forum=self.forum, user=self.user,
                                          name='Jaguar setup')

    def row(self):
        return SearchDocument.objects.get()

    def test_a_stale_read_does_not_overwrite_a_fresher_row(self):
        # What the slow task read, before the edit.
        stale_read = timezone.now()
        stale_copy = Topic.objects.get(pk=self.topic.pk)

        # The edit, and the task that read it, both land first.
        self.topic.name = 'Jazzmaster setup'
        self.topic.save()
        SearchDocument.objects.index_object(self.topic)
        self.assertEqual(self.row().title, 'Jazzmaster setup')

        # Now the slow one finishes, still holding the pre-edit name.
        SearchDocument.objects.index_object(stale_copy, read_at=stale_read)

        self.assertEqual(self.row().title, 'Jazzmaster setup')

    def test_a_stale_read_does_not_roll_indexed_at_backwards(self):
        # The reconcile sweep reads indexed_at, so a dropped write must not
        # leave the row looking older than the data actually in it.
        stale_read = timezone.now()
        stale_copy = Topic.objects.get(pk=self.topic.pk)
        fresh = SearchDocument.objects.index_object(self.topic)

        SearchDocument.objects.index_object(stale_copy, read_at=stale_read)

        self.assertEqual(self.row().indexed_at, fresh.indexed_at)

    def test_a_fresher_read_still_overwrites(self):
        # The guard must not block ordinary updates.
        SearchDocument.objects.index_object(self.topic)

        self.topic.name = 'Jazzmaster setup'
        self.topic.save()
        SearchDocument.objects.index_object(self.topic)

        self.assertEqual(self.row().title, 'Jazzmaster setup')

    def test_a_stale_read_still_creates_a_missing_row(self):
        # Nothing to lose to: an old read is better than no row at all.
        SearchDocument.objects.all().delete()

        SearchDocument.objects.index_object(
                self.topic, read_at=timezone.make_aware(datetime.datetime(2020, 1, 1)))

        self.assertEqual(self.row().title, 'Jaguar setup')
