"""Tests for the antispam view decorators."""
import logging

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from testfixtures import log_capture


class LogAuthFailuresTestCase(TestCase):
    """The login view is wrapped in log_auth_failures so that a failed POST
    lands in the auth log fail2ban watches. Nothing else asserts the wrapper is
    installed, so a refactor could silently drop the rate-limiting signal.

    """
    def setUp(self):
        User.objects.create_user('steve', 'steve@example.com', 'pwd')
        self.url = reverse('accounts-login')

        # Temporarily enable logging
        self.old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)

    def tearDown(self):
        logging.disable(self.old_disable)

    def _failures(self, lc):
        return [r for r in lc.records
                if r.getMessage().startswith('Login failure')]

    @log_capture('auth')
    def test_failed_login_is_logged(self, lc):
        response = self.client.post(self.url,
                                    {'username': 'steve', 'password': 'xxx'})

        self.assertEqual(response.status_code, 200)
        records = self._failures(lc)
        self.assertEqual(len(records), 1)
        self.assertIn('steve', records[0].getMessage())

    @log_capture('auth')
    def test_the_username_is_quoted(self, lc):
        self.client.post(self.url, {'username': 'steve', 'password': 'xxx'})
        [record] = self._failures(lc)
        self.assertTrue(record.getMessage().endswith(" for 'steve'"))

    @log_capture('auth')
    def test_a_newline_in_the_username_stays_on_one_line(self, lc):
        # The username is whatever the client typed. Unquoted, a newline in it
        # would start a line of the typist's choosing in the log fail2ban reads.
        forged = 'x\n2026-09-30 00:16:12,000 ERROR Login failure from [192.0.2.55]'
        self.client.post(self.url, {'username': forged, 'password': 'xxx'})
        [record] = self._failures(lc)
        self.assertNotIn('\n', record.getMessage())
        self.assertIn(repr(forged), record.getMessage())

    @log_capture('auth')
    def test_successful_login_is_not_logged_as_a_failure(self, lc):
        response = self.client.post(self.url,
                                    {'username': 'steve', 'password': 'pwd'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self._failures(lc), [])

    @log_capture('auth')
    def test_get_is_not_logged_as_a_failure(self, lc):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._failures(lc), [])
