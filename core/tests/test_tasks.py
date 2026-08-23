"""
Tests for the core tasks.

"""
import datetime
import logging
import smtplib

from django.conf import settings
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from unittest.mock import call, patch

import forums.unread
from accounts.models import EMAIL_CHANGE_EXPIRATION
from accounts.models import PendingEmailChange
from forums.models import Category, Forum, ForumLastVisit
from sg101.celery import app
from core.tasks import cleanup
from core.tasks import max_users
from core.email_categories import EmailCategory
from core.tasks import MAX_RETRIES, send_mail


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

    def test_cleanup_purges_expired_email_changes(self):
        # Unlike a registration confirmation, nobody is guaranteed to visit a
        # view that would purge these: a member who requests a change and never
        # confirms leaves the row behind forever. The daily sweep collects them.
        user = User.objects.create_user('paul', 'paul@example.com', 'pw')
        other = User.objects.create_user('eddie', 'eddie@example.com', 'pw')
        stale = PendingEmailChange.objects.request_change(user, 'a@example.com')
        PendingEmailChange.objects.filter(pk=stale.pk).update(
            date_requested=timezone.now() - EMAIL_CHANGE_EXPIRATION
                           - datetime.timedelta(minutes=1))
        fresh = PendingEmailChange.objects.request_change(other, 'b@example.com')

        cleanup.s().apply().get()

        self.assertEqual([c.pk for c in PendingEmailChange.objects.all()],
                         [fresh.pk])

    @patch('core.tasks.core.whos_online')
    def test_max_users(self, whos_online_mock):

        max_users.s().apply()

        self.assertEqual(whos_online_mock.mock_calls, [
            call.max_users(),
        ])


class SendMailRetryTestCase(TestCase):
    """The retry behaviour that a local mail server used to provide for us.

    Sending used to be a bare msg.send() with no retry, which was safe only
    because the far end was Postfix on localhost: it accepted in about a
    millisecond and then owned delivery, queueing and retrying for days.
    Sending through an external provider deletes that queue, so a transient
    network failure that used to be invisible becomes a lost message.

    Celery runs tasks eagerly under the test settings, so .apply() executes
    the retries inline and the countdown is ignored -- these run in
    milliseconds rather than the minutes the backoff would really take.
    """
    KWARGS = {
        'subject': 'Confirm your registration',
        'body': 'secret body text that must not be logged',
        'from_email': 'admin@surfguitar101.com',
        'to': ['member@example.com'],
    }

    def setUp(self):
        # The suite disables logging globally (settings/test.py) and that beats
        # assertLogs, whose records never reach its handler otherwise.
        self.old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, self.old_disable)

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_transient_failure_is_retried_until_it_succeeds(self, email_mock):
        email_mock.return_value.send.side_effect = [
            smtplib.SMTPException('connection reset'),
            smtplib.SMTPException('connection reset'),
            None,
        ]

        result = send_mail.s(**self.KWARGS).apply()

        self.assertEqual(email_mock.return_value.send.call_count, 3)
        self.assertTrue(result.successful())

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_socket_error_is_retried(self, email_mock):
        # EMAIL_TIMEOUT surfaces as a socket-level error rather than an SMTP
        # one, so OSError has to be in the transient list or a timeout would
        # never be retried.
        email_mock.return_value.send.side_effect = [OSError('timed out'), None]

        result = send_mail.s(**self.KWARGS).apply()

        self.assertEqual(email_mock.return_value.send.call_count, 2)
        self.assertTrue(result.successful())

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_refused_recipient_is_not_retried(self, email_mock):
        # SMTPRecipientsRefused subclasses SMTPException, so it is only kept
        # out of the retry path by being caught first. If that ordering is
        # ever reversed this test is what notices.
        email_mock.return_value.send.side_effect = \
            smtplib.SMTPRecipientsRefused({'member@example.com': (550, b'no')})

        result = send_mail.s(**self.KWARGS).apply()

        self.assertEqual(email_mock.return_value.send.call_count, 1)
        self.assertFalse(result.successful())

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_refused_sender_is_not_retried(self, email_mock):
        email_mock.return_value.send.side_effect = \
            smtplib.SMTPSenderRefused(550, b'not a verified sender',
                                      'admin@surfguitar101.com')

        result = send_mail.s(**self.KWARGS).apply()

        self.assertEqual(email_mock.return_value.send.call_count, 1)
        self.assertFalse(result.successful())

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_permanent_failure_is_logged_with_recipient_and_subject(
            self, email_mock):
        email_mock.return_value.send.side_effect = \
            smtplib.SMTPRecipientsRefused({'member@example.com': (550, b'no')})

        with self.assertLogs('email', level='ERROR') as logged:
            send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        self.assertEqual(len(logged.records), 1)
        message = logged.output[0]
        self.assertIn('member@example.com', message)
        self.assertIn('Confirm your registration', message)

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_exhausted_retries_give_up_and_log_at_error(self, email_mock):
        email_mock.return_value.send.side_effect = \
            smtplib.SMTPException('provider unreachable')

        with self.assertLogs('email', level='ERROR') as logged:
            result = send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        self.assertEqual(email_mock.return_value.send.call_count,
                         MAX_RETRIES + 1)
        self.assertFalse(result.successful())
        self.assertEqual(len(logged.records), 1)
        self.assertIn('member@example.com', logged.output[0])
        self.assertIn('Confirm your registration', logged.output[0])

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_failure_logs_never_contain_the_message_body(self, email_mock):
        # The log must not become the site's own copy of what it sent.
        email_mock.return_value.send.side_effect = \
            smtplib.SMTPException('provider unreachable')

        with self.assertLogs('email', level='ERROR') as logged:
            send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        for line in logged.output:
            self.assertNotIn('secret body text', line)


class SendMailLoggingTestCase(TestCase):
    """One line per message, carrying the outcome.

    The line is written where the send happens rather than where it is queued,
    so it can say what became of the message. A line written at dispatch could
    only report intent.
    """
    KWARGS = {
        'subject': 'Confirm your registration',
        'body': 'secret body text that must not be logged',
        'from_email': 'admin@surfguitar101.com',
        'to': ['member@example.com'],
    }

    def setUp(self):
        # The suite disables logging globally (settings/test.py) and that beats
        # assertLogs, whose records never reach its handler otherwise.
        self.old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, self.old_disable)

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_successful_send_logs_one_line(self, email_mock):
        with self.assertLogs('email', level='INFO') as logged:
            send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        self.assertEqual(len(logged.records), 1)
        line = logged.output[0]
        self.assertIn('category=registration', line)
        self.assertIn('to=member@example.com', line)
        self.assertIn('from=admin@surfguitar101.com', line)
        self.assertIn('outcome=sent', line)
        self.assertIn('Confirm your registration', line)

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_the_line_never_contains_the_body(self, email_mock):
        with self.assertLogs('email', level='INFO') as logged:
            send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        self.assertNotIn('secret body text', logged.output[0])

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_a_task_queued_without_a_category_still_runs(self, email_mock):
        # Celery can hold tasks serialized by the previous code across a
        # deploy. The default is what keeps that mail moving.
        with self.assertLogs('email', level='INFO') as logged:
            result = send_mail.s(**self.KWARGS).apply()

        self.assertTrue(result.successful())
        self.assertIn('category=uncategorized', logged.output[0])

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_category_is_not_passed_to_the_message(self, email_mock):
        # EmailMessage raises on an unexpected keyword, so category has to be
        # an explicit parameter rather than part of **kwargs.
        send_mail.s(category=EmailCategory.REGISTRATION, **self.KWARGS).apply()

        self.assertEqual(email_mock.mock_calls, [
            call(**self.KWARGS), call().send(),
        ])

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_member_authored_subjects_are_redacted(self, email_mock):
        kwargs = dict(self.KWARGS, subject='Re: your amp settings')

        with self.assertLogs('email', level='INFO') as logged:
            send_mail.s(category=EmailCategory.PM_NOTIFICATION, **kwargs).apply()

        self.assertIn('category=pm_notification', logged.output[0])
        self.assertIn('<redacted>', logged.output[0])
        self.assertNotIn('your amp settings', logged.output[0])

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_permanent_failure_says_so_in_the_line(self, email_mock):
        # Distinguishable by a value, not by the absence of a line.
        email_mock.return_value.send.side_effect = \
            smtplib.SMTPRecipientsRefused({'member@example.com': (550, b'no')})

        with self.assertLogs('email', level='INFO') as logged:
            send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        self.assertNotIn('outcome=sent', logged.output[0])
        self.assertIn('outcome=failed', logged.output[0])
        self.assertIn('category=registration', logged.output[0])

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_a_retry_is_logged_before_the_eventual_success(self, email_mock):
        email_mock.return_value.send.side_effect = [
            smtplib.SMTPException('connection reset'),
            None,
        ]

        with self.assertLogs('email', level='INFO') as logged:
            send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        outcomes = [line for line in logged.output if 'outcome=' in line]
        self.assertEqual(len(outcomes), 2)
        self.assertIn('outcome=retrying', outcomes[0])
        self.assertIn('outcome=sent', outcomes[1])

    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_giving_up_says_failed(self, email_mock):
        email_mock.return_value.send.side_effect = \
            smtplib.SMTPException('provider unreachable')

        with self.assertLogs('email', level='ERROR') as logged:
            send_mail.s(category=EmailCategory.REGISTRATION,
                        **self.KWARGS).apply()

        self.assertIn('outcome=failed', logged.output[-1])

    @patch('core.tasks.logger')
    @patch('core.tasks.django.core.mail.EmailMessage')
    def test_a_logging_failure_does_not_stop_the_send(self, email_mock,
                                                      logger_mock):
        # A broken log line must never cost someone their registration
        # confirmation.
        logger_mock.log.side_effect = ValueError('bad format string')

        result = send_mail.s(category=EmailCategory.REGISTRATION,
                             **self.KWARGS).apply()

        self.assertTrue(result.successful())
        self.assertEqual(email_mock.return_value.send.call_count, 1)


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
