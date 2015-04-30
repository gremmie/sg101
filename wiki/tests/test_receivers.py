"""Tests for the wiki app's signal handlers."""
import logging

from django.contrib.auth.models import User
from django.test import TestCase

from testfixtures import log_capture


class ReceiverTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')

        # Temporarily enable logging
        self.old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)

    def tearDown(self):
        logging.disable(self.old_disable)

    @log_capture('wiki.receivers')
    def test_signal_handlers(self, lc):
        # We don't have access to the dummy request that the test client creates
        # when logging in, so we can't really check to see if we added
        # attributes to the request object. But that code is pretty simple, so
        # lets just test that we logged something so we know our signal handlers
        # are hooked up and running.
        self.client.login(username='user', password='pw')
        self.client.logout()
        lc.check(('wiki.receivers', 'INFO', 'User login: user'),
                 ('wiki.receivers', 'INFO', 'User logout: user'))
