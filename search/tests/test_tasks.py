"""
Tests for the search application's Celery tasks, called directly.

The signal tests cover how these get queued; these cover what they do when
they run, including the races a queued task has to survive -- the object it
was queued for can be gone, or no longer belong in the index, by the time a
worker picks the task up.

"""
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType

from forums.models import Post
from forums.models import Topic
from search.models import SearchDocument
from search.tasks import reindex_category
from search.tasks import reindex_document
from search.tasks import remove_document
from search.tests.test_receivers import ReceiverTestCase
from weblinks.models import Link


class TaskTestCase(ReceiverTestCase):

    def content_type_id(self, model):
        return ContentType.objects.get_for_model(model).pk

    def reindex(self, obj):
        reindex_document(self.content_type_id(type(obj)), obj.pk)

    def test_reindexing_writes_the_row(self):
        self.reindex(self.story)

        row = self.rows_for(self.story).get()
        self.assertEqual(row.title, 'Convention roundup')
        self.assertIsNotNone(row.search_vector)

    def test_reindexing_stamps_indexed_at(self):
        # The reconcile sweep compares this against the source's update_date,
        # so a write that leaves it unset makes a fresh row look stale forever.
        self.reindex(self.story)

        self.assertIsNotNone(self.rows_for(self.story).get().indexed_at)

    def test_reindexing_an_object_that_is_already_gone_is_not_an_error(self):
        content_type_id = self.content_type_id(Post)
        object_id = self.post.pk
        self.post.delete()

        reindex_document(content_type_id, object_id)

        self.assertEqual(SearchDocument.objects.count(), 0)

    def test_reindexing_an_object_that_no_longer_belongs_removes_its_row(self):
        self.index(self.link)
        # update() rather than save(), so the row is only removed by the task
        # under test and not by the save that would have queued it.
        Link.objects.filter(pk=self.link.pk).update(is_public=False)

        self.reindex(self.link)

        self.assertNotIndexed(self.link)

    def test_reindexing_an_unsearchable_type_is_not_an_error(self):
        group = Group.objects.create(name='Kahunas')

        reindex_document(self.content_type_id(Group), group.pk)

        self.assertEqual(SearchDocument.objects.count(), 0)

    def test_reindexing_a_content_type_that_no_longer_exists_is_not_an_error(self):
        reindex_document(0, 1)

        self.assertEqual(SearchDocument.objects.count(), 0)

    def test_removing_deletes_the_row(self):
        self.index(self.item)

        remove_document(self.content_type_id(type(self.item)), self.item.pk)

        self.assertNotIndexed(self.item)

    def test_removing_a_row_that_is_not_there_is_not_an_error(self):
        remove_document(self.content_type_id(type(self.item)), self.item.pk)

        self.assertEqual(SearchDocument.objects.count(), 0)

    def test_the_write_tasks_retry_transient_database_errors(self):
        for task in (reindex_document, remove_document, reindex_category):
            with self.subTest(task=task.name):
                self.assertTrue(task.autoretry_for)
                self.assertEqual(task.retry_kwargs['max_retries'], 5)
                self.assertTrue(task.retry_backoff)


class CategoryTaskTestCase(ReceiverTestCase):

    def setUp(self):
        super().setUp()
        self.category = self.topic.forum.category
        self.group = Group.objects.create(name='Kahunas')

    def test_a_private_category_is_emptied_out_of_the_index(self):
        self.index(self.topic, self.post)
        self.category.groups.add(self.group)

        reindex_category(self.category.pk)

        self.assertNotIndexed(self.topic)
        self.assertNotIndexed(self.post)

    def test_a_public_category_is_filled_back_in(self):
        reindex_category(self.category.pk)

        self.assertIndexed(self.topic)
        self.assertIndexed(self.post)

    def test_another_categorys_content_is_left_alone(self):
        # The scope matters: a privacy change to one category must not reach
        # into the rows of another.
        other_forum = type(self.topic.forum).objects.create(
                category=type(self.category).objects.create(name='Gear',
                                                            slug='gear'),
                name='Amps', slug='amps')
        other_topic = Topic.objects.create(forum=other_forum, user=self.user,
                                           name='Blackface tone')
        self.index(other_topic)

        self.category.groups.add(self.group)
        reindex_category(self.category.pk)

        self.assertIndexed(other_topic)
