"""
Tests for the forums tasks.

"""
from django.test import TestCase
from mock import call, patch

from forums.tasks import new_post_task
from forums.tasks import updated_post_task
from forums.tasks import new_topic_task
from forums.tasks import updated_topic_task


class ForumsTasksTestCase(TestCase):
    @patch('forums.tasks.forums.latest')
    def test_new_post_task(self, latest_mock):

        new_post_task.s(42).apply()

        self.assertEquals(latest_mock.mock_calls, [
            call.process_new_post(42),
        ])

    @patch('forums.tasks.forums.latest')
    def test_updated_post_task(self, latest_mock):

        updated_post_task.s(42).apply()

        self.assertEquals(latest_mock.mock_calls, [
            call.process_updated_post(42),
        ])

    @patch('forums.tasks.forums.latest')
    def test_new_topic_task(self, latest_mock):

        new_topic_task.s(42).apply()

        self.assertEquals(latest_mock.mock_calls, [
            call.process_new_topic(42),
        ])

    @patch('forums.tasks.forums.latest')
    def test_updated_topic_task(self, latest_mock):

        updated_topic_task.s(42).apply()

        self.assertEquals(latest_mock.mock_calls, [
            call.process_updated_topic(42),
        ])
