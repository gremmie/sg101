"""Record every donation at the instant Paypal reported, not two hours early.

Paypal sends payment_date as a Pacific wall clock. The old parse discarded the
zone abbreviation and stamped the reading with TIME_ZONE (America/Chicago),
which is always two hours ahead of Pacific -- both zones observe daylight
saving together, so the error is a constant and not a seasonal one.

The corrected parse ships in the same deploy as this migration, so no database
can hold a correctly-stamped row before this runs: every row present came from
the old handler. That is why the boundary is simply the moment this is applied,
with no date to choose in advance and nothing to remember at release.

It assumes the database was built by a full load -- a fresh conversion of a
production snapshot, which is how the new host is brought up. Topping up an
already-migrated database with donations recorded later on the old site would
smuggle in uncorrected rows, and nothing here would find them.

"""
import datetime

from django.db import migrations
from django.db.migrations.recorder import MigrationRecorder
from django.db.models import F
from django.utils import timezone

NAME = '0002_payment_date_pacific_backfill'

SHIFT = datetime.timedelta(hours=2)


def shift_donations(Donation, boundary, delta):
    """Move every payment_date before `boundary` by `delta`."""
    return Donation.objects.filter(payment_date__lt=boundary).update(
            payment_date=F('payment_date') + delta)


def correct_to_pacific(apps, schema_editor):
    shift_donations(apps.get_model('donations', 'Donation'), timezone.now(),
                    SHIFT)


def back_to_chicago(apps, schema_editor):
    """Undo the correction over exactly the rows it touched.

    The boundary is recovered from Django's own record of when the forward ran
    rather than taken fresh, because a rollback after the site is live would
    otherwise walk back donations the corrected parse had recorded properly in
    the meantime.
    """
    applied = MigrationRecorder(schema_editor.connection).migration_qs.get(
            app='donations', name=NAME).applied
    shift_donations(apps.get_model('donations', 'Donation'), applied, -SHIFT)


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(correct_to_pacific, back_to_chicago),
    ]
