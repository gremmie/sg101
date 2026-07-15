"""Tests for the forum app's signal handlers."""

from django.contrib.auth.models import User
from django.test import TestCase

from mock import patch

from forums.models import Forum
from forums.models import Post
from forums.models import Topic


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
