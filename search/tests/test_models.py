"""Tests for the SearchDocument model and its schema."""

import datetime

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase

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
        before = datetime.datetime.now()
        doc = SearchDocument.objects.index_object(self.make_topic('Jaguar setup'))
        self.assertGreaterEqual(doc.indexed_at, before)
