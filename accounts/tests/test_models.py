"""
Tests for accounts.models -- registration-key generation and the
case-insensitive uniqueness of usernames.

PendingUserManager._make_key() builds the email-confirmation key with
base64 + sha1. That path relied on Py2-only text/bytes behavior
(unicode(), sha1(unicode), b64encode(str)) and was rewritten to be
dual-runtime; these lock in that create_pending_user() still yields a
well-formed key so the rewrite can't silently regress it.
"""
import re

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PendingUser


class MakeKeyTests(TestCase):

    def test_create_pending_user_generates_a_wellformed_key(self):
        pu = PendingUser.objects.create_pending_user(
            'newbie', 'newbie@example.com', 'secret')

        # sha1 hexdigest is 40 hex chars; [::2] keeps every other -> 20, which
        # is exactly the key field's max_length.
        self.assertEqual(len(pu.key), 20)
        self.assertTrue(re.match(r'^[0-9a-f]{20}$', pu.key),
                        msg='key is not 20 lowercase hex chars: %r' % pu.key)

    def test_keys_differ_between_registrations(self):
        # _make_key mixes in a random sample plus an incrementing counter, so
        # two registrations must not collide.
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
