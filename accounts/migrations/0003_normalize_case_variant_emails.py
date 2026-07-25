"""Lowercase the addresses that collide with another account only by case.

Thirteen addresses in the production database are held by two accounts each.
Twelve of those pairs are byte-identical -- two accounts genuinely sharing an
address, which predates this work and is left alone. One pair differs only in
capitalisation, so MySQL considers it a single address and Postgres would
consider it two. Folding it removes the last place where the two engines
disagree about who owns an address.

Only rows inside such a pair are touched. The other thousand-odd addresses
carrying uppercase are not collisions, and the case-insensitive lookups handle
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
