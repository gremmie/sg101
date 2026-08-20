"""
Tests for accounts.models -- registration-key generation and the
case-insensitive uniqueness of usernames.

The registration key is a CSPRNG token from accounts.utils. These lock in
its shape at the point registration actually mints one, so a change to the
manager cannot quietly reintroduce a derived or short key.
"""
import re

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PendingUser


class RegistrationKeyTests(TestCase):

    def test_create_pending_user_generates_a_urlsafe_token(self):
        pu = PendingUser.objects.create_pending_user(
            'newbie', 'newbie@example.com', 'secret')

        # Length is what discriminates: the old derived key was 20 characters
        # of lowercase hex, which also matches the URL-safe alphabet.
        self.assertGreaterEqual(len(pu.key), 32)
        self.assertTrue(re.match(r'^[A-Za-z0-9_-]+$', pu.key),
                        msg='key is not a URL-safe token: %r' % pu.key)

    def test_key_fits_the_column(self):
        pu = PendingUser.objects.create_pending_user(
            'newbie', 'newbie@example.com', 'secret')

        max_length = PendingUser._meta.get_field('key').max_length
        self.assertLessEqual(len(pu.key), max_length)

    def test_keys_differ_between_registrations(self):
        a = PendingUser.objects.create_pending_user('a', 'a@example.com', 'pw')
        b = PendingUser.objects.create_pending_user('b', 'b@example.com', 'pw')
        self.assertNotEqual(a.key, b.key)


class UsernameUniquenessTests(TestCase):
    """Usernames must be unique regardless of case, in the database itself.

    The registration form rejects case variants, but the form is not the only
    way a user is created -- the admin, a shell, and two simultaneous
    registrations all bypass it. Every engine enforces this, for two different
    reasons: MySQL because its case-insensitive collation already covers the
    plain UNIQUE on the column, Postgres and SQLite because of the functional
    unique index on LOWER(username).

    """

    def test_case_variant_username_is_rejected(self):
        User.objects.create_user('brianneal', 'brianneal@example.com', 'pw')

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user('BrianNeal', 'other@example.com', 'pw')

    def test_distinct_usernames_are_still_allowed(self):
        User.objects.create_user('brianneal', 'brianneal@example.com', 'pw')
        User.objects.create_user('brianneal2', 'other@example.com', 'pw')

        self.assertEqual(User.objects.count(), 2)
