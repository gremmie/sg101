"""
Models for the donations application.
"""
import datetime
import decimal

from django.db import models
from django.contrib import auth
from django.conf import settings


class DonationManager(models.Manager):
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
        today = datetime.date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        qs = self.filter(payment_date__year=year,
                payment_date__month=month,
                test_ipn=False).select_related('user')

        gross = decimal.Decimal()
        net = decimal.Decimal()
        donations = []
        for donation in qs:
            gross += donation.mc_gross
            net += donation.mc_gross - donation.mc_fee
            donations.append(donation)

        return gross, net, donations


class Donation(models.Model):
    """Model to represent a donation to the website."""

    user = models.ForeignKey(auth.models.User, null=True, blank=True)
    is_anonymous = models.BooleanField()
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

    def __unicode__(self):
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

