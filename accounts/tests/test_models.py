"""
Tests for accounts.models -- registration-key generation.

PendingUserManager._make_key() builds the email-confirmation key with
base64 + sha1. That path relied on Py2-only text/bytes behavior
(unicode(), sha1(unicode), b64encode(str)) and was rewritten to be
dual-runtime; these lock in that create_pending_user() still yields a
well-formed key so the rewrite can't silently regress it.
"""
import re

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
