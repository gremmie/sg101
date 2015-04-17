"""Tests for the antispam signal handlers."""
import logging

from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase

from testfixtures import log_capture


class AntispamSignalRcvrTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('steve', 'steve@example.com', 'pwd')
        self.client = Client()

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
                  'User login failed signal from django.contrib.auth: steve'))
