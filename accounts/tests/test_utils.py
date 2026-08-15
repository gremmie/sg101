"""
Tests for accounts.utils module.

"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from unittest.mock import call, patch, Mock

from accounts.models import PendingUser
from accounts.utils import create_new_user


class AccountUtilsTestCase(TestCase):
    fixtures = ['accounts.json']

    def setUp(self):
        self.pending_user = PendingUser(username='pjmoto',
            email='pjmoto@example.com', password='password')
        self.pending_user.save()

    def assert_new_user(self):
        pjmoto = User.objects.get(username='pjmoto')
        self.assertEqual(pjmoto.username, 'pjmoto')
        self.assertEqual(pjmoto.first_name, '')
        self.assertEqual(pjmoto.last_name, '')
        self.assertEqual(pjmoto.email, 'pjmoto@example.com')
        self.assertFalse(pjmoto.is_staff)
        self.assertTrue(pjmoto.is_active)
        self.assertFalse(pjmoto.is_superuser)

        now = timezone.now()
        delta = timedelta(days=0, seconds=5)
        self.assertTrue(now - pjmoto.last_login < delta)
        self.assertTrue(now - pjmoto.date_joined < delta)

        self.assertEqual(PendingUser.objects.count(), 0)

    @patch('accounts.utils.logger')
    def test_create_new_user_admin_activation(self, logger_mock):
        create_new_user(self.pending_user, admin_activation=True)

        self.assert_new_user()

        self.assertEqual(logger_mock.mock_calls, [
            call.info('Accounts registration confirmed by ADMIN for pjmoto')
        ])

    @patch('accounts.utils.logger')
    def test_create_new_user_user_activation(self, logger_mock):
        create_new_user(self.pending_user, ip='127.0.0.1',
                        admin_activation=False)

        self.assert_new_user()

        self.assertEqual(logger_mock.mock_calls, [
            call.info('Accounts registration confirmed by USER for pjmoto from '
                      '127.0.0.1')
        ])
