"""
Unit tests for the messages application views.

"""
from django.test import TestCase
from django.core.urlresolvers import reverse

from messages.models import Message, Options, Flag


VIEW_NAMES = [
    'messages-inbox',
    'messages-compose',
    'messages-outbox',
    'messages-trash',
    'messages-options',
    'messages-delete',
    'messages-undelete',
    'messages-view',
    'messages-report',
]


class NotLoggedInTestCase(TestCase):
    """Ensure we are redirected to the login page before we can do anything with
    this application.

    """
    LOGIN_URL = reverse('accounts-login')

    def _test_get(self, url_name, **kwargs):
        url = reverse(url_name, **kwargs)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + '?next=' + url)

    def _test_post(self, url_name, **kwargs):
        url = reverse(url_name, **kwargs)
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + '?next=' + url)

    def test_inbox(self):
        self._test_get('messages-inbox')

    def test_compose(self):
        url_name = 'messages-compose'
        self._test_get(url_name)
        self._test_post(url_name)

    def test_outbox(self):
        self._test_get('messages-outbox')

    def test_trash(self):
        self._test_get('messages-trash')

    def test_options(self):
        url_name = 'messages-options'
        self._test_get(url_name)
        self._test_post(url_name)

    def test_delete(self):
        self._test_get('messages-delete')

    def test_undelete(self):
        self._test_get('messages-undelete')

    def test_view(self):
        url_name = 'messages-view'
        self._test_get(url_name, args=[123])
        self._test_post(url_name, args=[123])

    def test_report(self):
        url_name = 'messages-report'
        self._test_get(url_name, args=[123])
        self._test_post(url_name, args=[123])
