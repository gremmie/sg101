"""Tests for what survives a post deletion.

`Forum.last_post` and `Topic.last_post` are denormalized pointers at a `Post`.
The foreign key sits on the parent pointing down at a child, so a cascade on it
travels parent-ward: deleting the post a forum points at deletes the forum, and
with it every topic and post inside. That has happened once, to a forum of
4,626 topics.

Three paths reach a post deletion and they are not equivalent. `post.delete()`
deletes one row. `QuerySet.delete()` reaches the same collector without going
through the model at all, which makes it the path that says whether `on_delete`
itself is safe. And the views decide between removing a post and removing its
whole topic before deleting anything. Each is covered here, because a test of
only the first proves the least interesting one.

"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from forums.models import Forum, Post, Topic
from forums.tools import delete_user_posts
from forums.views.main import delete_single_post


class DeletePathTestCase(TestCase):
    """A forum from the fixture, one topic, and posts to delete."""

    fixtures = ['forums.json']

    def setUp(self):
        self.user = User.objects.create_user('brian', 'brian@example.com', 'pw')
        self.forum = Forum.objects.get(pk=2)
        self.topic = Topic.objects.create(forum=self.forum, name='A Topic',
                                          user=self.user)

    def _post(self, body):
        """Creating a post updates both denormalized counts through the
        receivers, so `last_post` is current without setting it here.

        """
        return Post.objects.create(topic=self.topic, user=self.user, body=body)

    def _reload(self):
        self.forum.refresh_from_db()
        self.topic.refresh_from_db()


class CascadeTestCase(DeletePathTestCase):
    """The wrong-way cascade, from both delete paths."""

    def test_deleting_a_forums_last_post_leaves_the_forum_standing(self):
        first = self._post('first')
        last = self._post('last')
        self.forum.refresh_from_db()
        self.assertEqual(self.forum.last_post, last)

        last.delete()

        self.assertTrue(Forum.objects.filter(pk=self.forum.pk).exists())
        self.assertTrue(Post.objects.filter(pk=first.pk).exists())

    def test_a_queryset_delete_also_leaves_the_forum_standing(self):
        """The path that skips `Post.delete()` and exercises the collector on
        its own. `forums/tools.py` deletes this way.

        """
        self._post('first')
        last = self._post('last')

        Post.objects.filter(pk=last.pk).delete()

        self.assertTrue(Forum.objects.filter(pk=self.forum.pk).exists())

    def test_deleting_a_topics_last_post_leaves_the_topic_standing(self):
        """Two posts, so the override does not delete the topic for its own
        reasons and the only thing under test is the cascade.

        """
        self._post('first')
        last = self._post('last')
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.last_post, last)

        last.delete()

        self.assertTrue(Topic.objects.filter(pk=self.topic.pk).exists())

    def test_the_forums_last_post_moves_back_to_the_survivor(self):
        """Surviving is not enough: `on_post_delete` recomputes the pointer
        from what is left, so the forum index keeps showing a real post rather
        than an empty column.

        """
        first = self._post('first')
        last = self._post('last')

        last.delete()

        self._reload()
        self.assertEqual(self.forum.last_post, first)
        self.assertEqual(self.topic.last_post, first)

    def test_a_forum_with_nothing_left_reports_no_posts(self):
        """The sole post of the only topic, removed the way the site removes
        one. `delete_single_post` routes this case to `_delete_topic`, so the
        topic goes, the forum stays, and its pointer is left null -- which the
        forum index has always had a branch for.

        """
        self._post('only')

        delete_single_post(Post.objects.get())

        self.forum.refresh_from_db()
        self.assertIsNone(self.forum.last_post)
        self.assertFalse(Topic.objects.filter(pk=self.topic.pk).exists())
        response = self.client.get(reverse('forums-index'))
        self.assertContains(response, 'No posts')

    def test_deleting_a_posts_row_does_not_reach_its_topic(self):
        """Characterization, and the reason a dead branch went unnoticed for
        years. `Post.delete()` used to carry an `if this was the topic's first
        post: delete the topic` block that could never run, because Django
        nulls the instance's pk during the delete it compares against. Under
        the old cascade the topic went anyway whenever the post was its
        `last_post` -- which is what made the dead branch look alive, and what
        also took the forum. Deleting a post is now just that.

        """
        first = self._post('first')
        self._post('second')

        first.delete()

        self.assertTrue(Topic.objects.filter(pk=self.topic.pk).exists())
        self.assertEqual(self.topic.posts.count(), 1)


class PostDeleteReturnTestCase(DeletePathTestCase):
    """`Post.delete()` no longer overrides anything, so it answers what
    `Model.delete()` answers. It used to return None, which would have bitten
    the first caller to write `count, _ = post.delete()`.

    """
    def test_deleting_a_post_reports_what_it_deleted(self):
        self._post('first')
        post = self._post('second')

        count, per_model = post.delete()

        self.assertEqual(per_model['forums.Post'], 1)
        self.assertGreaterEqual(count, 1)


class DeleteUserPostsTestCase(DeletePathTestCase):
    """`delete_user_posts` bulk-deletes a member's posts. It repoints both
    `last_post` fields itself rather than calling `last_post_pre_delete`, then
    deletes as a queryset -- so it never runs the model's delete at all.

    """
    def setUp(self):
        super().setUp()
        self.other = User.objects.create_user('ivan', 'ivan@example.com', 'pw')

    def _post_by(self, user, body):
        return Post.objects.create(topic=self.topic, user=user, body=body)

    def test_the_forum_survives_losing_its_last_post(self):
        kept = self._post_by(self.other, 'theirs')
        self._post_by(self.user, 'mine')

        delete_user_posts(self.user)

        self._reload()
        self.assertTrue(Forum.objects.filter(pk=self.forum.pk).exists())
        self.assertEqual(self.forum.last_post, kept)
        self.assertEqual(self.forum.post_count, 1)

    def test_a_topic_that_loses_every_post_is_deleted(self):
        self._post_by(self.user, 'mine')

        delete_user_posts(self.user)

        self.assertFalse(Topic.objects.filter(pk=self.topic.pk).exists())
        self.forum.refresh_from_db()
        self.assertTrue(Forum.objects.filter(pk=self.forum.pk).exists())

    def test_another_members_posts_are_untouched(self):
        theirs = self._post_by(self.other, 'theirs')
        self._post_by(self.user, 'mine')

        delete_user_posts(self.user)

        self.assertTrue(Post.objects.filter(pk=theirs.pk).exists())

    def test_a_topic_whose_pointer_is_already_null_does_not_raise(self):
        """The two delete paths disagreed about whether `last_post` can be
        absent: the views guard the access and this function did not, though
        the field is nullable and is set to None whenever a count reaches zero.

        """
        self._post_by(self.other, 'theirs')
        self._post_by(self.user, 'mine')
        Topic.objects.filter(pk=self.topic.pk).update(last_post=None)

        delete_user_posts(self.user)

        self.assertTrue(Forum.objects.filter(pk=self.forum.pk).exists())

    def test_a_forum_whose_pointer_is_already_null_does_not_raise(self):
        self._post_by(self.other, 'theirs')
        self._post_by(self.user, 'mine')
        Forum.objects.filter(pk=self.forum.pk).update(last_post=None)

        delete_user_posts(self.user)

        self.assertTrue(Forum.objects.filter(pk=self.forum.pk).exists())
