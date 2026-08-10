"""Tests for the reindex_search management command."""


from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone

from forums.models import Category
from forums.models import Forum
from forums.models import Post
from forums.models import Topic
from search.models import SearchDocument
from search.tests.test_documents import DocumentTestCase
from ygroup.models import Post as YgroupPost


def reindex(*args):
    call_command('reindex_search', *args, verbosity=0)


def rows_for(model):
    """Returns the index rows for one source model."""
    return SearchDocument.objects.filter(
            content_type=ContentType.objects.get_for_model(model))


class ReindexTestCase(DocumentTestCase):
    """
    Runs against the one-of-each-type fixture the registry tests build, so a
    full sweep here covers all eight document types.

    """
    def test_full_sweep_indexes_every_type(self):
        reindex()

        self.assertEqual(SearchDocument.objects.count(), len(self.objects))
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                doc = rows_for(model).get(object_id=obj.pk)
                self.assertEqual(doc.content_object, obj)
                self.assertTrue(doc.title)

    def test_full_sweep_builds_the_vector(self):
        reindex()

        vectors = SearchDocument.objects.values_list('search_vector', flat=True)
        self.assertEqual(len(vectors), len(self.objects))
        self.assertTrue(all(vectors))

    def test_rerunning_updates_rather_than_accumulates(self):
        reindex()
        before = dict(SearchDocument.objects.values_list('pk', 'indexed_at'))

        reindex()
        after = dict(SearchDocument.objects.values_list('pk', 'indexed_at'))

        self.assertEqual(set(before), set(after))
        for pk, indexed_at in after.items():
            self.assertGreater(indexed_at, before[pk])

    def test_rerunning_picks_up_an_edit(self):
        reindex()
        self.ygroup_post.title = 'Jazzmaster thread'
        self.ygroup_post.save()

        reindex()

        doc = rows_for(YgroupPost).get(object_id=self.ygroup_post.pk)
        self.assertEqual(doc.title, 'Jazzmaster thread')
        self.assertIn('jazzmast', doc.search_vector)

    def test_a_deleted_object_loses_its_row(self):
        reindex()
        self.ygroup_post.delete()

        reindex()

        self.assertFalse(rows_for(YgroupPost).exists())
        self.assertEqual(SearchDocument.objects.count(), len(self.objects) - 1)

    def test_a_row_with_no_source_object_is_removed(self):
        reindex()
        orphan = rows_for(YgroupPost).get()
        orphan.pk = None
        orphan.object_id = 99999
        orphan.save()

        reindex()

        self.assertFalse(rows_for(YgroupPost).filter(object_id=99999).exists())

    def test_a_row_of_an_unsearchable_type_is_removed(self):
        SearchDocument.objects.create(
                content_type=ContentType.objects.get_for_model(User),
                object_id=self.user.pk, title='Not a document', url='/',
                date=timezone.now(),
                indexed_at=timezone.now())

        reindex()

        self.assertFalse(rows_for(User).exists())

    def test_selective_rebuild_leaves_other_types_alone(self):
        reindex()
        untouched = rows_for(Topic).get().indexed_at
        self.ygroup_post.title = 'Jazzmaster thread'
        self.ygroup_post.save()

        reindex('--model', 'ygroup.post')

        self.assertEqual(rows_for(YgroupPost).get().title, 'Jazzmaster thread')
        self.assertEqual(rows_for(Topic).get().indexed_at, untouched)

    def test_selective_rebuild_accepts_more_than_one_type(self):
        reindex('--model', 'ygroup.post', '--model', 'forums.topic')

        self.assertEqual(SearchDocument.objects.count(), 2)

    def test_an_unsearchable_model_is_an_error(self):
        with self.assertRaises(CommandError):
            reindex('--model', 'auth.user')

    def test_an_unknown_model_is_an_error(self):
        with self.assertRaises(CommandError):
            reindex('--model', 'nonesuch.thing')


class BatchingTestCase(TestCase):
    """
    The 463k-post table is the reason this command batches at all: it must
    stream its source rows and issue a bounded number of queries per batch
    rather than per object.

    """
    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.topics = [Topic.objects.create(forum=forum, user=self.user,
                                            name='Topic %d' % i)
                       for i in range(20)]

    def queries_for(self, *args):
        with CaptureQueriesContext(connection) as queries:
            reindex('--model', 'forums.topic', *args)
        return len(queries)

    def test_query_count_follows_batches_not_rows(self):
        # Twenty topics in batches of five cost the same as in batches of ten
        # would if queries were per row; they are not, so halving the batch
        # count halves the difference from the fixed per-run queries.
        five = self.queries_for('--batch-size', '5')
        ten = self.queries_for('--batch-size', '10')
        twenty = self.queries_for('--batch-size', '20')

        self.assertEqual(five - ten, 2 * (ten - twenty))
        self.assertLess(twenty, len(self.topics))

    def test_every_row_is_written_whatever_the_batch_size(self):
        for size in ['1', '3', '20', '1000']:
            with self.subTest(batch_size=size):
                reindex('--model', 'forums.topic', '--batch-size', size)
                self.assertEqual(rows_for(Topic).count(), len(self.topics))

    def test_a_batch_size_below_one_is_an_error(self):
        with self.assertRaises(CommandError):
            reindex('--model', 'forums.topic', '--batch-size', '0')


class PrivateCategoryTestCase(TestCase):
    """
    Production has one gated category, `Kahunas`, whose 487 topics and 19,088
    posts must never reach the index: there is no per-user filter at query
    time, so anything indexed is findable by anyone who can search.

    """
    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.public = self.make_forum('Main', 'main')
        self.private = self.make_forum('Kahunas', 'kahunas', private=True)

    def make_forum(self, name, slug, private=False):
        category = Category.objects.create(name=name, slug=slug)
        if private:
            category.groups.add(Group.objects.create(name='%s members' % name))
        return Forum.objects.create(category=category, name=name, slug=slug)

    def make_topic(self, forum, name):
        topic = Topic.objects.create(forum=forum, user=self.user, name=name)
        Post.objects.create(topic=topic, user=self.user, body='A reverb tank.')
        return topic

    def test_private_content_is_never_indexed(self):
        self.make_topic(self.public, 'Jaguar setup')
        self.make_topic(self.private, 'Secret setup')

        reindex()

        self.assertEqual([doc.title for doc in rows_for(Topic)],
                         ['Jaguar setup'])
        self.assertEqual([doc.title for doc in rows_for(Post)],
                         ['Jaguar setup'])

    def test_a_category_turning_private_loses_its_rows(self):
        topic = self.make_topic(self.public, 'Jaguar setup')
        reindex()
        self.assertTrue(rows_for(Topic).exists())

        self.public.category.groups.add(Group.objects.create(name='insiders'))
        reindex()

        self.assertFalse(rows_for(Topic).filter(object_id=topic.pk).exists())
        self.assertFalse(rows_for(Post).exists())

    def test_a_category_turning_public_gains_its_rows(self):
        topic = self.make_topic(self.private, 'Secret setup')
        reindex()
        self.assertFalse(rows_for(Topic).exists())

        self.private.category.groups.clear()
        reindex()

        self.assertTrue(rows_for(Topic).filter(object_id=topic.pk).exists())
        self.assertTrue(rows_for(Post).exists())
