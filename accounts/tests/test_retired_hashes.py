"""
Tests for retiring the password hashes Django no longer reads.

"""
import importlib

from django.apps import apps as global_apps
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

retire = importlib.import_module(
        'accounts.migrations.0009_retire_unreadable_password_hashes')

# MD5 of '123456', as eleven production accounts hold it, and a salted SHA1 in
# the format Django's old SHA1PasswordHasher wrote.
UNSALTED_MD5 = 'e10adc3949ba59abbe56e057f20f883e'
SALTED_SHA1 = 'sha1$a1b2c$' + 'f' * 40


class IsRetiredTestCase(SimpleTestCase):

    def test_retired(self):
        for value in (UNSALTED_MD5, UNSALTED_MD5.upper(), SALTED_SHA1):
            with self.subTest(value=value):
                self.assertTrue(retire.is_retired(value))

    def test_kept(self):
        for value in ('pbkdf2_sha256$1000000$salt$hash=', '!unusable', '',
                      UNSALTED_MD5[:31], UNSALTED_MD5 + '0', 'sha1'):
            with self.subTest(value=value):
                self.assertFalse(retire.is_retired(value))

    def test_django_reads_neither(self):
        # Why these go: no hasher in this Django identifies them, so neither
        # can ever be checked against a password again.
        for value in (UNSALTED_MD5, SALTED_SHA1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                identify_hasher(value)


class RetireTestCase(TestCase):

    def setUp(self):
        self.md5 = User.objects.create_user('md5_member', 'a@example.com')
        self.sha1 = User.objects.create_user('sha1_member', 'b@example.com')
        User.objects.filter(pk=self.md5.pk).update(password=UNSALTED_MD5)
        User.objects.filter(pk=self.sha1.pk).update(password=SALTED_SHA1)
        self.current = User.objects.create_user('current', 'c@example.com',
                                                'pw')

    def test_retired_hashes_become_unusable(self):
        retire.retire_unreadable_hashes(global_apps, None)

        for user in (self.md5, self.sha1):
            user.refresh_from_db()
            with self.subTest(username=user.username):
                self.assertFalse(user.has_usable_password())

    def test_each_gets_its_own_marker(self):
        retire.retire_unreadable_hashes(global_apps, None)

        self.md5.refresh_from_db()
        self.sha1.refresh_from_db()
        self.assertNotEqual(self.md5.password, self.sha1.password)

    def test_current_hash_untouched(self):
        before = self.current.password
        retire.retire_unreadable_hashes(global_apps, None)

        self.current.refresh_from_db()
        self.assertEqual(self.current.password, before)
        self.assertTrue(self.current.check_password('pw'))

    def test_account_otherwise_untouched(self):
        retire.retire_unreadable_hashes(global_apps, None)

        self.md5.refresh_from_db()
        self.assertTrue(self.md5.is_active)
        self.assertEqual(self.md5.email, 'a@example.com')
