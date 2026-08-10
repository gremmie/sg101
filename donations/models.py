"""
Models for the donations application.
"""
import decimal
from zoneinfo import ZoneInfo

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone


def in_month(qs, year, month):
    """
    Narrow a Donation queryset to one calendar month, read in TIME_ZONE.

    An instant only has a month once you say where you are standing, and a
    plain payment_date__month lookup reads it in whatever timezone happens to
    be active. That is TIME_ZONE today, because nothing activates one -- but a
    donation made at 7pm on the 31st is already the 1st in UTC, so if anything
    ever did activate a different zone, a donation would quietly move into the
    next month's report with nothing raised. Naming the zone settles it, and
    unlike a timezone.override() block it cannot be outlived by a lazy
    queryset: the zone is compiled into the SQL, not read when it runs.
    """
    site_tz = ZoneInfo(settings.TIME_ZONE)
    return qs.annotate(
            _payment_year=ExtractYear('payment_date', tzinfo=site_tz),
            _payment_month=ExtractMonth('payment_date', tzinfo=site_tz),
        ).filter(_payment_year=year, _payment_month=month)


class DonationManager(models.Manager):
    """Manager for the Donations model."""

    def monthly_stats(self, year=None, month=None):
        """
        Returns a tuple of items for the given month in the given
        year. If year is None, the current year is used. If month is None,
        the current month is used.
        The returned tuple has the following items, in order:
            (gross, net, donations)
        where:
            'gross': total gross donations
            'net': total net donations
            'donations': list of donation objects
        """
        today = timezone.localdate()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        qs = in_month(self, year, month).filter(
                test_ipn=settings.DONATIONS_DEBUG).order_by(
                        'payment_date').select_related('user')

        gross = decimal.Decimal()
        net = decimal.Decimal()
        donations = []
        for donation in qs:
            gross += donation.mc_gross
            net += donation.mc_gross - donation.mc_fee
            donations.append(donation)

        return gross, net, donations

    def monthly_goal_pct(self, year=None, month=None, limit=True):
        """Returns progress towards the given monthly goal as an integer
        percent.

        If year is None, the current year is used.
        If month is None, the current month is used.
        If limit is True, the return value is limited to 100.

        """
        today = timezone.localdate()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        r = in_month(self, year, month).aggregate(
                Sum('mc_gross'), Sum('mc_fee'))

        gross, fee = r['mc_gross__sum'], r['mc_fee__sum']

        if gross is not None and fee is not None:
            pct = int((gross - fee) / settings.DONATIONS_GOAL * 100)
        else:
            pct = 0

        if limit:
            pct = min(pct, 100)

        return pct

    def top_donors(self, n=10):
        """Returns a list of the top n donors as user objects that have a
        total_donations field annotation.

        The data is taken from non anonymous donations from logged in users.

        """
        qs = User.objects.filter(donation__isnull=False,
                                 donation__is_anonymous=False) \
                .distinct() \
                .annotate(total_donations=Sum('donation__mc_gross')) \
                .order_by('-total_donations')[:n]

        return qs


class Donation(models.Model):
    """Model to represent a donation to the website."""

    user = models.ForeignKey(User, null=True, blank=True,
                             on_delete=models.CASCADE)
    is_anonymous = models.BooleanField(default=False)
    test_ipn = models.BooleanField(default=False, verbose_name="Test IPN")
    txn_id = models.CharField(max_length=20, verbose_name="Txn ID")
    txn_type = models.CharField(max_length=64)
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, blank=True)
    payer_email = models.EmailField(max_length=127, blank=True)
    payer_id = models.CharField(max_length=13, blank=True, verbose_name="Payer ID")
    mc_fee = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Fee")
    mc_gross = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Gross")
    memo = models.TextField(blank=True)
    payer_status = models.CharField(max_length=10, blank=True)
    payment_date = models.DateTimeField()

    objects = DonationManager()

    class Meta:
        ordering = ('-payment_date', )

    def __str__(self):
        if self.user:
            return u'%s from %s' % (self.mc_gross, self.user.username)
        return u'%s from %s %s' % (self.mc_gross, self.first_name, self.last_name)

    def donor(self):
        """Returns the donor name for the donation."""
        if self.is_anonymous:
            return settings.DONATIONS_ANON_NAME
        if self.user is not None:
            return self.user.username
        if self.first_name or self.last_name:
            name = u'%s %s' % (self.first_name, self.last_name)
            return name.strip()
        return settings.DONATIONS_ANON_NAME

