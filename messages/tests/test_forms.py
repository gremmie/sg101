"""Unit tests for the messages application forms."""

from django.contrib.auth.models import User
from django.test import TestCase

from messages.forms import ComposeForm


class ComposeFormTestCase(TestCase):
    fixtures = ['messages_test_users.json']

    def test_unsafe_image(self):
        data = {
            'receiver': 'pj',
            'subject': 'Test subject',
            'message': 'Hi ![image](http:example.com/a.jpg)',
        }
        user = User.objects.get(username='eddie')
        f = ComposeForm(user, data)
        self.assertFalse(f.is_valid())

    def test_receiver_differing_case(self):
        # The recipient is typed by hand (the autocomplete only assists), so
        # a case-sensitive lookup here rejects a name that plainly exists.
        data = {
            'receiver': 'PJ',
            'subject': 'Test subject',
            'message': 'Hi there',
        }
        user = User.objects.get(username='eddie')
        f = ComposeForm(user, data)
        self.assertTrue(f.is_valid(), msg=f.errors.as_text())
        self.assertEqual(f.rcvr_user.username, 'pj')

    def test_unknown_receiver(self):
        data = {
            'receiver': 'nobody',
            'subject': 'Test subject',
            'message': 'Hi there',
        }
        user = User.objects.get(username='eddie')
        f = ComposeForm(user, data)
        self.assertFalse(f.is_valid())

