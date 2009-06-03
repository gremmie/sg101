"""
Models for the donations application.
"""
from django.db import models
from django.contrib import auth

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

    class Meta:
        ordering = ('-payment_date', )

    def __unicode__(self):
        if self.user:
            return u'%s from %s' % (self.mc_gross, self.user.username)
        return u'%s from %s %s' % (self.mc_gross, self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        if self.user is None:
            self.is_anonymous = True
        super(Donation, self).save(*args, **kwargs)
