"""Tests for the antispam signal handlers."""
import logging

from django.contrib.auth.models import User
from django.test import TestCase

from testfixtures import log_capture


class AntispamSignalRcvrTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('steve', 'steve@example.com', 'pwd')

        # Temporarily enable logging
        self.old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)

    def tearDown(self):
        logging.disable(self.old_disable)

    @log_capture('auth')
    def test_login_logout_callback(self, lc):
        self.assertTrue(self.client.login(username='steve', password='pwd'))
        self.client.logout()
        lc.check(('auth', 'INFO', 'User login signal: steve'),
                 ('auth', 'INFO', 'User logout signal: steve'))

    @log_capture('auth')
    def test_login_failed_callback(self, lc):
        self.assertFalse(self.client.login(username='steve', password='xxx'))
        lc.check(('auth', 'ERROR',
                  "User login failed signal from django.contrib.auth: 'steve'"))

    @log_capture('auth')
    def test_a_newline_in_the_username_stays_on_one_line(self, lc):
        # The username is whatever the client typed. Unquoted, a newline in it
        # would start a line of the typist's choosing in the log fail2ban reads.
        forged = 'x\n2026-09-30 00:16:12,000 ERROR Login failure from [192.0.2.55]'
        self.assertFalse(self.client.login(username=forged, password='xxx'))
        [record] = lc.records
        self.assertNotIn('\n', record.getMessage())
        self.assertIn(repr(forged), record.getMessage())
