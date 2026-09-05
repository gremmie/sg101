"""Lowercase the addresses that collide with another account only by case.

Some addresses are held by more than one account. Most such groups are
byte-identical -- accounts genuinely sharing an address, which predates this
work and is left alone here. A group differing only in capitalisation is a
different thing: MySQL considers it one address and Postgres considers it two,
so folding it removes the last place where the two engines disagree about who
owns an address.

Note what that does to the groups that follow. Folding a case variant makes its
group byte-identical too, so this migration leaves *more* genuinely-shared
addresses than it found -- clearing those is 0008's job, not this one's. An
earlier version of this docstring counted the groups it inherited, which read
ever after as a count of what it left behind, and cost real time to untangle.

Only rows inside such a group are touched. Addresses carrying uppercase that
collide with nothing are not collisions, and the case-insensitive lookups handle
them.
"""
from collections import defaultdict

from django.db import migrations


def normalize(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # Grouped and compared in Python on purpose. Doing it in the database would
    # mean comparing strings on the very engine whose comparison semantics are
    # in question -- on MySQL, `exclude(email=x)` excludes the case variants
    # too, and the migration would quietly do nothing.
    groups = defaultdict(list)
    for pk, email in User.objects.exclude(email='').values_list('pk', 'email'):
        groups[email.lower()].append((pk, email))

    for lowered, rows in groups.items():
        if len(rows) < 2:
            continue
        for pk, email in rows:
            if email != lowered:
                User.objects.filter(pk=pk).update(email=lowered)


def noop(apps, schema_editor):
    # The original capitalisation is not recoverable, and does not matter once
    # every lookup is case-insensitive.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auth_user_username_lower_unique'),
    ]

    operations = [
        migrations.RunPython(normalize, noop),
    ]
