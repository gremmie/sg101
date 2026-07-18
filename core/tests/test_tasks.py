"""
Tests for the core tasks.

"""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from mock import call, patch

import forums.unread
from forums.models import Category, Forum, ForumLastVisit
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

    def test_cleanup_runs_and_purges_stale_forum_visits(self):
        # cleanup delegates to the clearsessions + forum_cleanup management
        # commands. Invoking a command's execute() directly (as this task once
        # did) raises KeyError 'no_color' under Django 1.10+, so run the task and
        # .get() its result to surface such an error instead of letting it hide
        # inside the task result. The stale ForumLastVisit proves forum_cleanup
        # actually ran.
        cat = Category.objects.create(name='Cat', slug='cat')
        forum = Forum.objects.create(category=cat, name='Forum', slug='forum')
        user = User.objects.create_user('u', '', 'pw')
        stale = (datetime.datetime.now() - forums.unread.THRESHOLD * 2
                 - datetime.timedelta(days=1))
        flv = ForumLastVisit.objects.create(user=user, forum=forum,
                                            begin_date=stale, end_date=stale)

        cleanup.s().apply().get()

        self.assertFalse(ForumLastVisit.objects.filter(pk=flv.pk).exists())

    @patch('core.tasks.core.whos_online')
    def test_max_users(self, whos_online_mock):

        max_users.s().apply()

        self.assertEquals(whos_online_mock.mock_calls, [
            call.max_users(),
        ])
