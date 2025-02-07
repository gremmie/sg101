"""
Tests for the core tasks.

"""
from django.test import TestCase
from mock import call, patch

from core.tasks import cleanup
from core.tasks import max_users
from core.tasks import send_mail


class CoreTasksTestCase(TestCase):
    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_send_mail(self, email_mock):

        kwargs = {'a': 1, 'b': 2, 'c':3}
        send_mail.s(**kwargs).apply()

        self.assertEquals(email_mock.mock_calls, [
            call(**kwargs),
            call().send(),
        ])

    """
    Can't get this to work... :(
    @patch('django.contrib.sessions.management.commands.clearsessions')
    @patch('forums.management.commands.forum_cleanup')
    def test_cleanup(self, forum_cleanup_mock, clearsessions_mock):

        cleanup.s().apply()

        self.assertEquals(clearsessions.mock_calls, [
            # TODO
        ])
        self.assertEquals(forum_cleanup_mock.mock_calls, [
            # TODO
        ])
    """

    @patch('core.tasks.core.whos_online')
    def test_max_users(self, whos_online_mock):

        max_users.s().apply()

        self.assertEquals(whos_online_mock.mock_calls, [
            call.max_users(),
        ])
