"""
Tests for the search application's signal handlers.

These are the tests that have to fail if indexing is queued anywhere other than
on commit, so most of them run inside captureOnCommitCallbacks and check that
nothing has reached the index until the block ends. Under eager Celery a
delay() called straight from a handler would index immediately, which is
exactly what those assertions catch -- an ordinary test that only looked at the
end state would pass either way.

"""
from unittest import mock

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from elsewhere.models import WebsiteProfile

from bio.models import UserProfile
from downloads.models import Download
from forums.models import Post
from forums.models import Topic
from forums.tools import delete_user_posts
from forums.views.main import _delete_topic
from search.models import SearchDocument
from search.tests.test_documents import DocumentTestCase
from weblinks.models import Link


class ReceiverTestCase(DocumentTestCase):
    """Adds the index-row helpers the signal tests share."""

    def rows_for(self, obj):
        """The index rows pointing at obj -- one if it is indexed, none if not."""
        return SearchDocument.objects.filter(
                content_type=ContentType.objects.get_for_model(type(obj)),
                object_id=obj.pk)

    def assertIndexed(self, obj):
        self.assertTrue(self.rows_for(obj).exists(),
                        "%s is not in the index" % type(obj).__name__)

    def assertNotIndexed(self, obj):
        self.assertFalse(self.rows_for(obj).exists(),
                         "%s is still in the index" % type(obj).__name__)

    def index(self, *objects):
        """Puts objects in the index directly, as a precondition."""
        for obj in objects:
            SearchDocument.objects.index_object(obj)


class OnCommitTestCase(ReceiverTestCase):

    def test_nothing_is_indexed_until_the_transaction_commits(self):
        with self.captureOnCommitCallbacks(execute=True):
            post = Post.objects.create(topic=self.topic, user=self.user,
                                       body='A second reverb tank.')
            # The handler has run by now. If it queued the task itself rather
            # than deferring it, eager Celery has already written the row.
            self.assertNotIndexed(post)

        self.assertIndexed(post)

    def test_a_rolled_back_save_queues_nothing(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            try:
                with transaction.atomic():
                    Post.objects.create(topic=self.topic, user=self.user,
                                        body='This post is not going to last.')
                    raise RuntimeError('rolling back')
            except RuntimeError:
                pass

        self.assertEqual(callbacks, [])
        self.assertEqual(SearchDocument.objects.count(), 0)

    def test_a_save_queues_its_reindex_once(self):
        with self.captureOnCommitCallbacks() as callbacks:
            self.item.save()

        self.assertEqual(len(callbacks), 1)


class IndexMaintenanceTestCase(ReceiverTestCase):

    def test_saving_indexes_every_type(self):
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                with self.captureOnCommitCallbacks(execute=True):
                    obj.save()
                self.assertIndexed(obj)

    def test_editing_rewrites_the_row(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.story.save()
        self.assertEqual(self.rows_for(self.story).get().title,
                         'Convention roundup')

        self.story.title = 'Convention roundup, part two'
        with self.captureOnCommitCallbacks(execute=True):
            self.story.save()

        self.assertEqual(self.rows_for(self.story).get().title,
                         'Convention roundup, part two')

    def test_deleting_removes_the_row(self):
        # The forums are left out here and covered on their own below: their
        # objects delete each other through last_post and the topic foreign
        # key, which is worth testing deliberately rather than incidentally.
        deletable = [obj for model, obj in self.objects.items()
                     if model not in (Topic, Post)]
        self.index(*deletable)

        for obj in deletable:
            with self.subTest(model=type(obj).__name__):
                self.assertIndexed(obj)
                with self.captureOnCommitCallbacks(execute=True):
                    obj.delete()
                self.assertNotIndexed(obj)

    def test_deleting_a_post_removes_only_its_own_row(self):
        second = Post.objects.create(topic=self.topic, user=self.user,
                                     body='A follow up about the tank.')
        self.index(self.topic, self.post, second)

        with self.captureOnCommitCallbacks(execute=True):
            self.post.delete()

        self.assertNotIndexed(self.post)
        self.assertIndexed(second)
        self.assertIndexed(self.topic)

    def test_deleting_a_topic_removes_its_posts_rows_too(self):
        # Through the forums' own delete-a-topic path, which deletes the posts
        # in bulk: a queryset delete fires post_delete per row, so the rows go
        # with them rather than being orphaned.
        second = Post.objects.create(topic=self.topic, user=self.user,
                                     body='A follow up about the tank.')
        self.index(self.topic, self.post, second)

        with self.captureOnCommitCallbacks(execute=True):
            _delete_topic(self.topic)

        self.assertEqual(SearchDocument.objects.filter(
            content_type__app_label='forums').count(), 0)

    def test_deleting_a_members_posts_removes_their_rows(self):
        # The forums' spam tool, which deletes a member's posts in bulk and
        # takes any topic left empty with them.
        self.index(self.topic, self.post)

        with self.captureOnCommitCallbacks(execute=True):
            delete_user_posts(self.user)

        self.assertEqual(SearchDocument.objects.filter(
            content_type__app_label='forums').count(), 0)

    def test_indexing_cannot_break_the_thing_being_saved(self):
        # A bug in building a document must cost the index a row, not stop a
        # member from posting. This is the whole reason indexing is a task.
        with mock.patch('search.documents.PostDocument.build',
                        side_effect=ValueError('bad document')):
            with self.captureOnCommitCallbacks(execute=True):
                post = Post.objects.create(topic=self.topic, user=self.user,
                                           body='The post still has to land.')

        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
        self.assertNotIndexed(post)


class PrivacyTestCase(ReceiverTestCase):

    def setUp(self):
        super().setUp()
        self.category = self.topic.forum.category
        self.group = Group.objects.create(name='Kahunas')

    def test_making_a_category_private_purges_its_content(self):
        self.index(self.topic, self.post)

        with self.captureOnCommitCallbacks(execute=True):
            self.category.groups.add(self.group)

        self.assertNotIndexed(self.topic)
        self.assertNotIndexed(self.post)

    def test_making_a_category_public_again_indexes_its_content(self):
        self.category.groups.add(self.group)

        with self.captureOnCommitCallbacks(execute=True):
            self.category.groups.remove(self.group)

        self.assertIndexed(self.topic)
        self.assertIndexed(self.post)

    def test_clearing_a_categorys_groups_indexes_its_content(self):
        self.category.groups.add(self.group)

        with self.captureOnCommitCallbacks(execute=True):
            self.category.groups.clear()

        self.assertIndexed(self.topic)
        self.assertIndexed(self.post)

    def test_a_group_gaining_a_category_purges_it(self):
        # The same relation edited from the group's side.
        self.index(self.topic, self.post)

        with self.captureOnCommitCallbacks(execute=True):
            self.group.category_set.add(self.category)

        self.assertNotIndexed(self.topic)
        self.assertNotIndexed(self.post)

    def test_posting_to_a_private_category_indexes_nothing(self):
        self.category.groups.add(self.group)

        with self.captureOnCommitCallbacks(execute=True):
            topic = Topic.objects.create(forum=self.topic.forum, user=self.user,
                                         name='Private jaguar talk')
            post = Post.objects.create(topic=topic, user=self.user,
                                       body='Members only reverb.')

        self.assertNotIndexed(topic)
        self.assertNotIndexed(post)


class ApprovalTestCase(ReceiverTestCase):

    def test_unapproving_a_link_removes_its_row(self):
        self.index(self.link)

        self.link.is_public = False
        with self.captureOnCommitCallbacks(execute=True):
            self.link.save()

        self.assertNotIndexed(self.link)

    def test_approving_a_download_indexes_it(self):
        unapproved = Download.objects.create(
                category=self.download.category, title='Unreleased tab',
                description='Not approved yet.', file='downloads/x.txt',
                user=self.user, ip_address='127.0.0.1')

        with self.captureOnCommitCallbacks(execute=True):
            unapproved.save()
        self.assertNotIndexed(unapproved)

        unapproved.is_public = True
        with self.captureOnCommitCallbacks(execute=True):
            unapproved.save()

        self.assertIndexed(unapproved)

    def test_deactivating_a_member_removes_their_profile_row(self):
        self.index(self.profile)

        # Straight through the user record, the way the auth admin does it --
        # the profile itself is untouched.
        self.user.is_active = False
        with self.captureOnCommitCallbacks(execute=True):
            self.user.save()

        self.assertNotIndexed(self.profile)

    def test_renaming_a_member_rewrites_their_profile_row(self):
        self.index(self.profile)

        self.user.last_name = 'Kahuna'
        with self.captureOnCommitCallbacks(execute=True):
            self.user.save()

        self.assertIn('Kahuna', self.rows_for(self.profile).get().title)

    def test_adding_a_website_link_rewrites_the_profile_row(self):
        # The links live in their own model, so adding one never saves the
        # profile whose document indexes it.
        self.index(self.profile)

        with self.captureOnCommitCallbacks(execute=True):
            WebsiteProfile.objects.create(user=self.user, name='surfrider.example',
                                          url='http://surfrider.example/')

        self.assertIn('surfrider.example',
                      self.rows_for(self.profile).get().summary)

    def test_deleting_a_website_link_rewrites_the_profile_row(self):
        site = WebsiteProfile.objects.get(user=self.user)
        self.index(self.profile)
        self.assertIn('kahunasurf.example.com',
                      self.rows_for(self.profile).get().summary)

        with self.captureOnCommitCallbacks(execute=True):
            site.delete()

        self.assertNotIn('kahunasurf.example.com',
                         self.rows_for(self.profile).get().summary)

    def test_a_login_queues_nothing(self):
        with self.captureOnCommitCallbacks() as callbacks:
            self.user.last_login = self.user.date_joined
            self.user.save(update_fields=['last_login'])

        self.assertEqual(callbacks, [])

    def test_creating_a_user_indexes_the_profile_it_creates(self):
        with self.captureOnCommitCallbacks(execute=True):
            user = User.objects.create_user('wahini', 'w@example.com', 'pw')

        self.assertIndexed(UserProfile.objects.get(user=user))
