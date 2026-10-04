"""
Tests for logging in by username without regard to case.

"""
from unittest.mock import patch

from django.contrib.auth import aauthenticate, authenticate
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse


class CaseInsensitiveLoginTestCase(TestCase):
    """A member logs in as their name typed in any case.

    MySQL's case-insensitive collation gave jaguar this for free; on PostgreSQL
    Django's own backend matches the name exactly, so `kojack` found no account
    named `Kojack`.
    """

    def setUp(self):
        self.user = User.objects.create_user('Kojack', '', 'pw')

    def test_login_view_other_case(self):
        response = self.client.post(reverse('accounts-login'),
                                    {'username': 'kojack', 'password': 'pw'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']),
                         self.user.pk)

    def test_authenticate_other_case(self):
        for name in ('kojack', 'KOJACK', 'kOjAcK'):
            with self.subTest(name=name):
                self.assertEqual(authenticate(username=name, password='pw'),
                                 self.user)

    def test_authenticate_exact_case(self):
        self.assertEqual(authenticate(username='Kojack', password='pw'),
                         self.user)

    async def test_aauthenticate_other_case(self):
        user = await aauthenticate(username='kojack', password='pw')
        self.assertEqual(user, self.user)

    def test_non_ascii_other_case(self):
        user = User.objects.create_user('Iñaki', '', 'pw')
        self.assertEqual(authenticate(username='iÑaki', password='pw'), user)

    def test_wrong_password(self):
        self.assertIsNone(authenticate(username='kojack', password='nope'))

    def test_no_such_user(self):
        self.assertIsNone(authenticate(username='nobody', password='pw'))

    def test_no_such_user_still_hashes(self):
        # Refusing a missing account must cost what refusing a wrong password
        # does, or the time taken tells which names exist (Django #20760).
        with patch.object(User, 'set_password') as set_password:
            authenticate(username='nobody', password='pw')
        set_password.assert_called_once_with('pw')

    def test_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(authenticate(username='kojack', password='pw'))

    def test_missing_credentials(self):
        self.assertIsNone(authenticate(username='kojack'))
        self.assertIsNone(authenticate(password='pw'))

    def test_lookup_uses_the_lower_index(self):
        # auth_user_username_lower_uniq (accounts 0002) is on LOWER(username).
        # Django's __iexact compiles to UPPER() = UPPER(), which that index
        # cannot serve; the lookup has to be written against LOWER to use it.
        with CaptureQueriesContext(connection) as ctx:
            authenticate(username='kojack', password='pw')
        sql = ctx.captured_queries[0]['sql']
        self.assertIn('LOWER("auth_user"."username")', sql)
        self.assertNotIn('UPPER', sql)
