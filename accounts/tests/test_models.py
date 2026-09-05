"""
Tests for accounts.models -- registration-key generation, the
case-insensitive uniqueness of usernames and addresses, and pending email
address changes.

The registration key is a CSPRNG token from accounts.utils. These lock in
its shape at the point registration actually mints one, so a change to the
manager cannot quietly reintroduce a derived or short key.
"""
import datetime
import re

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import EMAIL_CHANGE_EXPIRATION
from accounts.models import PendingEmailChange
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


class EmailUniquenessTests(TestCase):
    """An address belongs to one account, regardless of case -- except a blank.

    The same argument as for usernames: the registration and profile forms both
    reject an address another account holds, and neither is the only way a user
    is written. The partial functional index on LOWER(email) states it where the
    admin and a shell cannot go around it.

    Blank is the deliberate exception. Anonymous, which absorbed the posts of
    every user deleted under the site's phpBB predecessor, must never carry an
    address, and it is not the only account holding none.

    """

    def test_case_variant_email_is_rejected(self):
        User.objects.create_user('one', 'shared@example.com', 'pw')

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user('two', 'Shared@Example.com', 'pw')

    def test_distinct_emails_are_still_allowed(self):
        User.objects.create_user('one', 'one@example.com', 'pw')
        User.objects.create_user('two', 'two@example.com', 'pw')

        self.assertEqual(User.objects.count(), 2)

    def test_any_number_of_accounts_may_hold_no_address(self):
        User.objects.create_user('one', '', 'pw')
        User.objects.create_user('two', '', 'pw')
        User.objects.create_user('three', '', 'pw')

        self.assertEqual(User.objects.filter(email='').count(), 3)


class PendingEmailChangeTests(TestCase):
    """The pending-change row, its key, and the one-day window.

    The OneToOneField is the last-request-wins rule expressed in the schema:
    there is no application code that deletes a previous request, because the
    database cannot hold two.

    """

    def setUp(self):
        self.user = User.objects.create_user('paul', 'paul@example.com', 'pw')

    def test_request_change_generates_a_urlsafe_token(self):
        change = PendingEmailChange.objects.request_change(
            self.user, 'new@example.com')

        # Length is what discriminates here, exactly as it does for the
        # registration key: 20 characters of lowercase hex would satisfy the
        # alphabet too.
        self.assertGreaterEqual(len(change.key), 32)
        self.assertTrue(re.match(r'^[A-Za-z0-9_-]+$', change.key),
                        msg='key is not a URL-safe token: %r' % change.key)
        self.assertLessEqual(
            len(change.key),
            PendingEmailChange._meta.get_field('key').max_length)

    def test_a_second_request_replaces_the_first(self):
        first = PendingEmailChange.objects.request_change(
            self.user, 'first@example.com')
        second = PendingEmailChange.objects.request_change(
            self.user, 'second@example.com')

        self.assertEqual(PendingEmailChange.objects.count(), 1)
        self.assertEqual(second.new_email, 'second@example.com')
        self.assertNotEqual(second.key, first.key)

    def test_purge_expired_deletes_expired_and_keeps_fresh(self):
        other = User.objects.create_user('eddie', 'eddie@example.com', 'pw')
        stale = PendingEmailChange.objects.request_change(
            self.user, 'stale@example.com')
        PendingEmailChange.objects.filter(pk=stale.pk).update(
            date_requested=timezone.now() - EMAIL_CHANGE_EXPIRATION
                           - datetime.timedelta(minutes=1))
        fresh = PendingEmailChange.objects.request_change(
            other, 'fresh@example.com')

        PendingEmailChange.objects.purge_expired()

        self.assertEqual([c.pk for c in PendingEmailChange.objects.all()],
                         [fresh.pk])

    def test_is_expired_and_active_agree_on_the_window(self):
        change = PendingEmailChange.objects.request_change(
            self.user, 'new@example.com')

        self.assertFalse(change.is_expired)
        self.assertEqual(PendingEmailChange.objects.active().count(), 1)

        PendingEmailChange.objects.filter(pk=change.pk).update(
            date_requested=timezone.now() - EMAIL_CHANGE_EXPIRATION
                           - datetime.timedelta(minutes=1))
        change.refresh_from_db()

        self.assertTrue(change.is_expired)
        self.assertEqual(PendingEmailChange.objects.active().count(), 0)
