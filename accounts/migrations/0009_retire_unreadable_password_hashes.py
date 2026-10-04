"""Replace the password hashes Django can no longer read with unusable ones.

Two formats survive from the old site's early years: a bare unsalted MD5, 32 hex
digits, and Django's old salted `sha1$salt$hash`. The old site's Django read
both, and re-hashed a password whenever its owner logged in, so these are
exactly the accounts nobody has logged in to since: on the production snapshot
of 2026-10-04, 2,662 MD5 accounts (last login 2011-02-24) and 1,234 SHA1 ones
(last login 2012-05-06).

This Django ships neither hasher, so neither can be checked against a password
again; their owners get in only by resetting the password, which they can still
do. What the hashes can still do is give up the passwords behind them: unsalted
MD5 above all, where eleven accounts share the hash of `123456`. Every copy of
the database and every backup carries them. Replacing each with an unusable
marker changes nothing for the member and removes the hash.

The accounts are otherwise untouched: they stay active, keep their addresses and
posts, and can reset their password as before.

"""
import re

from django.contrib.auth.hashers import make_password
from django.db import migrations

UNSALTED_MD5 = re.compile(r'[0-9a-f]{32}', re.IGNORECASE)


def is_retired(password):
    """True if password is a hash in one of the formats this retires."""
    return bool(UNSALTED_MD5.fullmatch(password)
                or password.startswith('sha1$'))


def retire_unreadable_hashes(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # Matched in Python rather than with a database regex, so what is retired
    # is decided by the one function the tests exercise.
    users = [user for user in User.objects.only('pk', 'password')
             if is_retired(user.password)]
    for user in users:
        # A fresh marker each: make_password(None) is '!' and random text.
        user.password = make_password(None)
    User.objects.bulk_update(users, ['password'], batch_size=500)


def noop(apps, schema_editor):
    # The hashes are gone, and restoring them would only put back what this
    # migration exists to remove.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_auth_user_email_lower_unique'),
    ]

    operations = [
        migrations.RunPython(retire_unreadable_hashes, noop),
    ]
