"""Give an email address one owner, and clear the pairs standing in the way.

The registration form and the profile form both reject an address another
account already holds, but neither is the only way a user is written -- the
admin and a management shell go around both, which is the same argument the
username index in 0002 was built on. This states it where they cannot.

The index is partial, and permanently so. Some accounts hold no address at all,
among them the Anonymous account inherited from the site's phpBB predecessor,
which absorbed the posts of every deleted user and must never carry one. A plain
unique index cannot express that; `WHERE email <> ''` can.

An address held by more than one account keeps whichever logged in most
recently; the rest are left with no address. Those accounts are otherwise
untouched -- they keep their posts, their profiles and their ability to log in,
and lose only self-serve password reset until someone gives them an address
back.

The groups are computed rather than listed. The database this runs against is
not the one it was written against: a snapshot taken later may hold a group this
author never saw, and listing today's would silently skip it.

"""
import datetime
from collections import defaultdict

from django.db import migrations

INDEX_NAME = 'auth_user_email_lower_uniq'

# Sorts before any real timestamp, so an account that has never logged in ranks
# below one that has without needing a branch.
_NEVER = datetime.datetime(datetime.MINYEAR, 1, 1, tzinfo=datetime.timezone.utc)


def _rank(row):
    pk, _email, last_login = row
    # Most recent login wins; ties -- including a group where nobody has ever
    # logged in -- go to the lowest pk. An account that has never logged in
    # needs no term of its own: _NEVER sorts below every real timestamp. Only
    # the plain case occurs in the production data.
    return (last_login or _NEVER, -pk)


def plan_blanking(rows):
    """Which pks must lose their address, given (pk, email, last_login) rows.

    Kept a pure function over rows rather than a queryset walk: it is the half
    that decides which member loses something, and the index this migration
    installs forbids the rows a database-level test would have to set up.
    """
    groups = defaultdict(list)
    for row in rows:
        _pk, email, _last_login = row
        if email:
            groups[email.lower()].append(row)

    blank = set()
    for members in groups.values():
        if len(members) < 2:
            continue
        keeper, _email, _last_login = max(members, key=_rank)
        blank.update(pk for pk, _e, _l in members if pk != keeper)
    return blank


def blank_duplicate_addresses(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # Grouped in Python for the reason 0003 gives: comparing addresses in the
    # database means comparing them on the very engine whose comparison
    # semantics are in question.
    rows = User.objects.exclude(email='').values_list('pk', 'email',
                                                      'last_login')
    to_blank = plan_blanking(rows)
    if to_blank:
        User.objects.filter(pk__in=to_blank).update(email='')


def noop(apps, schema_editor):
    # Which account held the address is not recoverable once it is
    # gone, and re-creating the duplicate would only re-break the index this
    # migration exists to build. Restoring one means deciding again, with the
    # same evidence, so it belongs to a person rather than to a reverse.
    pass


def create_index(apps, schema_editor):
    # MySQL 5.7 has no functional indexes. Unlike the username case its
    # collation does not cover this one -- there is no UNIQUE on email to make
    # case-insensitive -- but the old engine is being retired rather than
    # constrained, and the blanking above still runs.
    if schema_editor.connection.vendor == 'mysql':
        return

    schema_editor.execute(
        "CREATE UNIQUE INDEX %s ON auth_user (LOWER(email)) "
        "WHERE email <> ''" % INDEX_NAME)


def drop_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'mysql':
        return

    schema_editor.execute('DROP INDEX %s' % INDEX_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_pendingemailchange'),
    ]

    operations = [
        migrations.RunPython(blank_duplicate_addresses, noop),
        migrations.RunPython(create_index, drop_index),
    ]
