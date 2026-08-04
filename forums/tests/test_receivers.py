"""Tests for the forum app's signal handlers."""

from django.contrib.auth.models import User
from django.test import TestCase

from mock import patch

from forums.models import Forum
from forums.models import Post
from forums.models import Topic
from forums.signals import notify_new_post
from forums.signals import notify_new_topic
from forums.signals import notify_updated_post
from forums.signals import notify_updated_topic


class ReceiverTestCase(TestCase):

    fixtures = ['forums.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')

    @patch('forums.latest.notify_topic_delete')
    def test_signal_handlers(self, mock_latest):
        forum = Forum.objects.get(pk=2)
        topic = Topic(forum=forum,
                      name='Test Topic',
                      user=self.user)
        topic.save()
        forum = Forum.objects.get(pk=2)
        self.assertEqual(1, forum.topic_count)

        post = Post(topic=topic, user=self.user, body='test')
        post.save()

        topic = Topic.objects.get(pk=topic.pk)
        self.assertEqual(topic.post_count, 1)
        forum = Forum.objects.get(pk=2)
        self.assertEqual(forum.post_count, 1)

        # To prevent cascading deletes
        topic.last_post_pre_delete()
        topic.save()
        forum.last_post_pre_delete()
        forum.save()

        post.delete()
        topic = Topic.objects.get(pk=topic.pk)
        self.assertEqual(topic.post_count, 0)
        forum = Forum.objects.get(pk=2)
        self.assertEqual(forum.post_count, 0)

        topic.delete()
        forum = Forum.objects.get(pk=2)
        self.assertEqual(0, forum.topic_count)

        mock_latest.assert_called_once_with(topic)


class ContentUpdateSignalTestCase(TestCase):
    """The content-update signals must carry the 'created' argument.

    The handlers in forums.latest read kwargs['created'] directly, and the
    notify helpers send with send_robust, which swallows the resulting
    KeyError. A dropped argument therefore costs a queued task and reports
    nothing, so it is worth pinning which task each helper reaches.
    """

    fixtures = ['forums.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')
        self.topic = Topic.objects.create(forum=Forum.objects.get(pk=2),
                                          name='Test Topic',
                                          user=self.user)
        self.post = Post.objects.create(topic=self.topic, user=self.user,
                                        body='test')

    @patch('forums.tasks.new_topic_task')
    def test_new_topic_queues_new_topic_task(self, task):
        notify_new_topic(self.topic)
        task.delay.assert_called_once_with(self.topic.id)

    @patch('forums.tasks.updated_topic_task')
    def test_updated_topic_queues_updated_topic_task(self, task):
        notify_updated_topic(self.topic)
        task.delay.assert_called_once_with(self.topic.id)

    @patch('forums.tasks.new_post_task')
    def test_new_post_queues_new_post_task(self, task):
        notify_new_post(self.post)
        task.delay.assert_called_once_with(self.post.id)

    @patch('forums.tasks.updated_post_task')
    def test_updated_post_queues_updated_post_task(self, task):
        notify_updated_post(self.post)
        task.delay.assert_called_once_with(self.post.id)
