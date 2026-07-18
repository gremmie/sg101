"""
Characterization tests for the forums read/unread tracking.

``forums.unread`` is the algorithm behind the "has unread" indicators on forums,
topics, and posts, plus the "topics with unread posts" page. It drives a central
part of the user experience, so these tests lock in its current behavior to guard
against regressions.

Read tracking works off two per-user bookkeeping records:

* ``ForumLastVisit`` (flv) -- a window ``[begin_date, end_date]`` per (user, forum).
  Posts newer than ``end_date`` are unread; posts older than ``begin_date`` are
  read; anything inside the window needs per-topic inspection. ``begin == end``
  means "all caught up".
* ``TopicLastVisit`` (tlv) -- a ``last_visit`` timestamp per (user, topic).

The helpers below create topics/posts/records with explicit timestamps so each
scenario pins one branch of that algorithm.
"""
import datetime

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from forums.models import (Forum, ForumLastVisit, Post, Topic,
                           TopicLastVisit)
from forums.unread import (get_forum_unread_status, get_post_unread_status,
                           get_topic_unread_status, get_unread_topics)


NOW = datetime.datetime.now()
DAY = datetime.timedelta(days=1)


def make_topic_at(forum, user, when, name='a topic'):
    """Create a topic whose single post (and thus update_date) is at ``when``."""
    topic = Topic.objects.create(forum=forum, name=name, user=user)
    post = Post.objects.create(topic=topic, user=user, body='first post')
    _stamp(post, when)
    _resync(topic)
    return Topic.objects.get(pk=topic.pk), Post.objects.get(pk=post.pk)


def add_post_at(topic, user, when, body='a reply'):
    """Append a reply dated ``when`` and refresh the denormalized fields."""
    post = Post.objects.create(topic=topic, user=user, body=body)
    _stamp(post, when)
    _resync(topic)
    return Post.objects.get(pk=post.pk)


def _stamp(post, when):
    # Post.save only auto-sets dates on insert, so re-saving keeps our values.
    post.creation_date = when
    post.update_date = when
    post.save()


def _resync(topic):
    # Recompute the topic/forum denormalized last_post + update_date from posts.
    topic.post_count_update()
    topic.save()
    topic.forum.post_count_update()
    topic.forum.save()


def make_flv(user, forum, begin, end):
    return ForumLastVisit.objects.create(user=user, forum=forum,
                                         begin_date=begin, end_date=end)


class GetPostUnreadStatusTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.reader = User.objects.create_user('reader', '', 'pw')

    def test_anonymous_sees_nothing_unread(self):
        from django.contrib.auth.models import AnonymousUser
        topic, post = make_topic_at(self.forum, self.author, NOW)
        get_post_unread_status(topic, [post], AnonymousUser())
        self.assertFalse(post.unread)

    def test_no_forum_last_visit_means_all_read(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        get_post_unread_status(topic, [post], self.reader)
        self.assertFalse(post.unread)

    def test_posts_entirely_before_window_are_read(self):
        topic, post = make_topic_at(self.forum, self.author, NOW - 10 * DAY)
        # Window opened after the last post -> everything already read.
        make_flv(self.reader, self.forum, NOW - 2 * DAY, NOW)
        get_post_unread_status(topic, [post], self.reader)
        self.assertFalse(post.unread)

    def test_without_tlv_posts_after_end_date_are_unread(self):
        topic, old_post = make_topic_at(self.forum, self.author, NOW - 5 * DAY)
        new_post = add_post_at(topic, self.author, NOW)
        # Window ends 3 days ago; no per-topic visit record.
        make_flv(self.reader, self.forum, NOW - 6 * DAY, NOW - 3 * DAY)
        get_post_unread_status(topic, [old_post, new_post], self.reader)
        self.assertFalse(old_post.unread)   # before end_date
        self.assertTrue(new_post.unread)    # after end_date

    def test_with_tlv_posts_after_last_visit_are_unread(self):
        topic, old_post = make_topic_at(self.forum, self.author, NOW - 5 * DAY)
        new_post = add_post_at(topic, self.author, NOW)
        make_flv(self.reader, self.forum, NOW - 6 * DAY, NOW)
        TopicLastVisit.objects.create(user=self.reader, topic=topic,
                                      last_visit=NOW - 2 * DAY)
        get_post_unread_status(topic, [old_post, new_post], self.reader)
        self.assertFalse(old_post.unread)   # read before last_visit
        self.assertTrue(new_post.unread)    # posted after last_visit


class GetTopicUnreadStatusTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.reader = User.objects.create_user('reader', '', 'pw')

    def test_anonymous_sees_nothing_unread(self):
        from django.contrib.auth.models import AnonymousUser
        topic, post = make_topic_at(self.forum, self.author, NOW)
        forum = Forum.objects.get(pk=self.forum.pk)  # refresh last_post
        get_topic_unread_status(forum, [topic], AnonymousUser())
        self.assertFalse(topic.has_unread)

    def test_missing_flv_is_created_and_marks_all_read(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        forum = Forum.objects.get(pk=self.forum.pk)
        self.assertFalse(ForumLastVisit.objects.filter(
            user=self.reader, forum=forum).exists())

        get_topic_unread_status(forum, [topic], self.reader)

        self.assertFalse(topic.has_unread)
        self.assertTrue(ForumLastVisit.objects.filter(
            user=self.reader, forum=forum).exists())

    def test_topic_updated_after_window_is_unread(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        forum = Forum.objects.get(pk=self.forum.pk)
        make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW - 2 * DAY)
        get_topic_unread_status(forum, [topic], self.reader)
        self.assertTrue(topic.has_unread)

    def test_topic_updated_before_window_is_read(self):
        topic, post = make_topic_at(self.forum, self.author, NOW - 10 * DAY)
        recent, _ = make_topic_at(self.forum, self.author, NOW, name='recent')
        forum = Forum.objects.get(pk=self.forum.pk)   # last_post is now recent
        make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW)
        get_topic_unread_status(forum, [topic], self.reader)
        self.assertFalse(topic.has_unread)

    def test_topic_in_window_with_fresh_tlv_is_read(self):
        topic, post = make_topic_at(self.forum, self.author, NOW - DAY)
        forum = Forum.objects.get(pk=self.forum.pk)
        make_flv(self.reader, self.forum, NOW - 3 * DAY, NOW)
        TopicLastVisit.objects.create(user=self.reader, topic=topic,
                                      last_visit=NOW)
        get_topic_unread_status(forum, [topic], self.reader)
        self.assertFalse(topic.has_unread)

    def test_topic_in_window_without_tlv_is_unread(self):
        topic, post = make_topic_at(self.forum, self.author, NOW - DAY)
        forum = Forum.objects.get(pk=self.forum.pk)
        make_flv(self.reader, self.forum, NOW - 3 * DAY, NOW)
        get_topic_unread_status(forum, [topic], self.reader)
        self.assertTrue(topic.has_unread)


class GetForumUnreadStatusTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.reader = User.objects.create_user('reader', '', 'pw')

    def test_anonymous_sees_nothing_unread(self):
        from django.contrib.auth.models import AnonymousUser
        make_topic_at(self.forum, self.author, NOW)
        forum = Forum.objects.get(pk=self.forum.pk)
        get_forum_unread_status([forum], AnonymousUser())
        self.assertFalse(forum.has_unread)

    def test_empty_forum_has_no_unread(self):
        forum = Forum.objects.get(pk=self.forum.pk)   # no posts -> last_post None
        self.assertIsNone(forum.last_post)
        get_forum_unread_status([forum], self.reader)
        self.assertFalse(forum.has_unread)

    def test_missing_flv_is_created_and_marks_read(self):
        make_topic_at(self.forum, self.author, NOW)
        forum = Forum.objects.get(pk=self.forum.pk)
        get_forum_unread_status([forum], self.reader)
        self.assertFalse(forum.has_unread)
        self.assertTrue(ForumLastVisit.objects.filter(
            user=self.reader, forum=forum).exists())

    def test_last_post_after_window_end_is_unread(self):
        make_topic_at(self.forum, self.author, NOW)
        forum = Forum.objects.get(pk=self.forum.pk)
        make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW - 2 * DAY)
        get_forum_unread_status([forum], self.reader)
        self.assertTrue(forum.has_unread)

    def test_last_post_before_window_start_is_read(self):
        make_topic_at(self.forum, self.author, NOW - 5 * DAY)
        forum = Forum.objects.get(pk=self.forum.pk)
        make_flv(self.reader, self.forum, NOW - 2 * DAY, NOW)
        get_forum_unread_status([forum], self.reader)
        self.assertFalse(forum.has_unread)


class GetUnreadTopicsTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.reader = User.objects.create_user('reader', '', 'pw')

    def test_anonymous_gets_empty_list(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertEqual(get_unread_topics(AnonymousUser()), [])

    def test_topic_newer_than_visit_window_is_returned(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW - 5 * DAY)
        unread = get_unread_topics(self.reader)
        self.assertIn(topic, unread)

    def test_topic_with_current_tlv_is_not_returned(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW - 5 * DAY)
        TopicLastVisit.objects.create(user=self.reader, topic=topic,
                                      last_visit=NOW + DAY)
        unread = get_unread_topics(self.reader)
        self.assertNotIn(topic, unread)


class UnreadJourneyTests(TestCase):
    """View-level journeys that drive the read-tracking machinery."""
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.reader = User.objects.create_user('reader', '', 'pw')

    def test_topic_unread_anonymous_redirects_to_topic(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        response = self.client.get(reverse('forums-topic_unread', args=[topic.id]))
        self.assertRedirects(
            response, reverse('forums-topic_index', kwargs={'id': str(topic.id)}),
            fetch_redirect_response=False)

    def test_topic_unread_without_records_redirects_to_topic(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        self.client.login(username='reader', password='pw')
        response = self.client.get(reverse('forums-topic_unread', args=[topic.id]))
        self.assertEqual(response.status_code, 302)
        # Plain topic URL, no per-post anchor.
        self.assertNotIn('#p', response['Location'])

    def test_topic_unread_jumps_to_first_unread_post(self):
        topic, first = make_topic_at(self.forum, self.author, NOW - 3 * DAY)
        newer = add_post_at(topic, self.author, NOW)
        # Reader last saw the topic before the newer post.
        make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW)
        TopicLastVisit.objects.create(user=self.reader, topic=topic,
                                      last_visit=NOW - DAY)
        self.client.login(username='reader', password='pw')

        response = self.client.get(reverse('forums-topic_unread', args=[topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('#p%s' % newer.id, response['Location'])

    def test_forum_catchup_marks_forum_read(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW)
        TopicLastVisit.objects.create(user=self.reader, topic=topic,
                                      last_visit=NOW - 2 * DAY)
        self.client.login(username='reader', password='pw')

        response = self.client.post(reverse('forums-catchup', kwargs={'slug': self.forum.slug}))
        self.assertEqual(response.status_code, 302)

        flv = ForumLastVisit.objects.get(user=self.reader, forum=self.forum)
        self.assertTrue(flv.is_caught_up())
        self.assertFalse(TopicLastVisit.objects.filter(
            user=self.reader, topic=topic).exists())

    def test_catchup_all_marks_every_forum_read(self):
        make_topic_at(self.forum, self.author, NOW)
        flv = make_flv(self.reader, self.forum, NOW - 5 * DAY, NOW)
        self.assertFalse(flv.is_caught_up())
        self.client.login(username='reader', password='pw')

        response = self.client.post(reverse('forums-catchup_all'))
        self.assertEqual(response.status_code, 302)

        flv = ForumLastVisit.objects.get(user=self.reader, forum=self.forum)
        self.assertTrue(flv.is_caught_up())

    def test_visiting_topic_creates_forum_last_visit(self):
        topic, post = make_topic_at(self.forum, self.author, NOW)
        self.client.login(username='reader', password='pw')
        self.assertFalse(ForumLastVisit.objects.filter(
            user=self.reader, forum=self.forum).exists())

        response = self.client.get(reverse('forums-topic_index', kwargs={'id': str(topic.id)}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ForumLastVisit.objects.filter(
            user=self.reader, forum=self.forum).exists())
