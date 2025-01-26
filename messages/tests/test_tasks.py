"""
Unit tests for the messages application tasks.

"""
import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from messages.models import Message, Options, Flag
from messages.tasks import purge_messages


class PurgeMessagesTaskTestCase(TestCase):
    """Testing the purge messages celery task."""
    fixtures = ['messages_test_users.json']

    def setUp(self):
        now = datetime.datetime.now()
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
        task = purge_messages.s().apply()
        self.assertEqual(Message.objects.all().count(), 0)
