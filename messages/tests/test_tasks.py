"""
Unit tests for the messages application tasks.

"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from messages.models import Message, Options, Flag
from messages.tasks import purge_messages


class PurgeMessagesTaskTestCase(TestCase):
    """Testing the purge messages celery task."""
    fixtures = ['messages_test_users.json']

    def setUp(self):
        now = timezone.now()
        pj = User.objects.get(username='pj')
        eddie = User.objects.get(username='eddie')
        pm = Message(sender=pj,
                     receiver=eddie,
                     send_date=now,
                     read_date=now,
                     subject='Test',
                     message='Message',
                     sender_delete_date=now,
                     receiver_delete_date=now)
        pm.save()

    def test_purge_command(self):
        self.assertEqual(Message.objects.all().count(), 1)
        # .get() re-raises any exception from the task body; without it a failure
        # in the task (e.g. the command wrapper raising) would hide here and show
        # only as the count assertion below not matching.
        purge_messages.s().apply().get()
        self.assertEqual(Message.objects.all().count(), 0)
