"""
Unit tests for the messages application models.

"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from messages.models import Message


class UnreadCountTestCase(TestCase):
    """Tests for MessageManager.unread_count()."""
    fixtures = ['messages_test_users.json']

    def setUp(self):
        self.pj = User.objects.get(username='pj')
        self.eddie = User.objects.get(username='eddie')

    def _send(self, sender, receiver, subject='Test'):
        return Message.objects.create(sender=sender, receiver=receiver,
                                      subject=subject, message='Hello')

    def test_no_messages(self):
        self.assertEqual(Message.objects.unread_count(self.pj), 0)

    def test_unread_message_counts(self):
        self._send(self.eddie, self.pj)
        self.assertEqual(Message.objects.unread_count(self.pj), 1)

    def test_read_message_does_not_count(self):
        msg = self._send(self.eddie, self.pj)
        msg.read_date = timezone.now()
        msg.save()
        self.assertEqual(Message.objects.unread_count(self.pj), 0)

    def test_sent_message_does_not_count_for_sender(self):
        self._send(self.pj, self.eddie)
        self.assertEqual(Message.objects.unread_count(self.pj), 0)

    def test_deleted_unread_message_does_not_count(self):
        # Deleting an unread message moves it to the trash without stamping
        # read_date, so the count must exclude it the way inbox() does.
        # Otherwise the receiver is told they have a new message with nothing
        # in their inbox to read, and no way to clear it from the inbox.
        msg = self._send(self.eddie, self.pj)
        msg.receiver_delete_date = timezone.now()
        msg.save()

        self.assertEqual(Message.objects.inbox(self.pj).count(), 0)
        self.assertEqual(Message.objects.unread_count(self.pj), 0)

    def test_count_matches_unread_messages_in_inbox(self):
        read = self._send(self.eddie, self.pj, subject='Read')
        read.read_date = timezone.now()
        read.save()
        deleted = self._send(self.eddie, self.pj, subject='Deleted')
        deleted.receiver_delete_date = timezone.now()
        deleted.save()
        self._send(self.eddie, self.pj, subject='Unread')

        inbox_unread = sum(1 for m in Message.objects.inbox(self.pj) if m.unread())
        self.assertEqual(Message.objects.unread_count(self.pj), inbox_unread)
        self.assertEqual(Message.objects.unread_count(self.pj), 1)
