"""
Tests for the core tasks.

"""
import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from unittest.mock import call, patch

import forums.unread
from forums.models import Category, Forum, ForumLastVisit
from sg101.celery import app
from core.tasks import cleanup
from core.tasks import max_users
from core.tasks import send_mail


class CoreTasksTestCase(TestCase):
    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_send_mail(self, email_mock):

        kwargs = {'a': 1, 'b': 2, 'c':3}
        send_mail.s(**kwargs).apply()

        self.assertEqual(email_mock.mock_calls, [
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
        stale = (timezone.now() - forums.unread.THRESHOLD * 2
                 - datetime.timedelta(days=1))
        flv = ForumLastVisit.objects.create(user=user, forum=forum,
                                            begin_date=stale, end_date=stale)

        cleanup.s().apply().get()

        self.assertFalse(ForumLastVisit.objects.filter(pk=flv.pk).exists())

    @patch('core.tasks.core.whos_online')
    def test_max_users(self, whos_online_mock):

        max_users.s().apply()

        self.assertEqual(whos_online_mock.mock_calls, [
            call.max_users(),
        ])


class BeatScheduleTestCase(SimpleTestCase):
    """The scheduled entries must name tasks that exist.

    Beat resolves a task by name at fire time, so an entry naming something the
    registry does not have fails in the worker log -- for the Sunday-morning
    jobs, up to a week after the rename that broke it. Renaming a task out from
    under this schedule has cost this project a broken scheduled job before, and
    nothing else in the suite reads the setting: every task here has its own
    tests, and all of them call the task directly.

    `import_default_modules()` forces the autodiscovery that is otherwise lazy,
    so the registry is fully populated rather than however full the tests that
    happened to run first left it.
    """
    def setUp(self):
        app.loader.import_default_modules()

    def test_every_scheduled_entry_names_a_registered_task(self):
        self.assertTrue(settings.CELERY_BEAT_SCHEDULE, 'schedule is empty')
        for name, entry in sorted(settings.CELERY_BEAT_SCHEDULE.items()):
            with self.subTest(entry=name):
                self.assertIn(entry['task'], app.tasks)

    def test_every_scheduled_entry_has_a_schedule(self):
        # A missing 'schedule' key is an entry beat will refuse to load at all,
        # and it reads as plausible in a diff next to the tasks around it.
        for name, entry in sorted(settings.CELERY_BEAT_SCHEDULE.items()):
            with self.subTest(entry=name):
                self.assertIn('schedule', entry)
