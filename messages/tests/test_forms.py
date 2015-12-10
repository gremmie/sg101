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

