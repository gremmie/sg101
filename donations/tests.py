"""
Tests for the donations application.
"""
import urlparse
from decimal import Decimal
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from donations.models import Donation
import bio.badges


# This data was copy/pasted from my actual Paypal IPN history. Some alterations
# were made since this file is getting committed to version control and I
# didn't want to store "real" data that could be used to trace a transaction or
# real payer.

# This data is for a non-anonymous donation:
TEST_POST_DATA_1 = """\
mc_gross=5.00&protection_eligibility=Ineligible&payer_id=FAKEPAYERID01&tax=0.00&payment_date=04:14:08 Jan 21, 2011 PST&payment_status=Completed&charset=windows-1252&first_name=John&option_selection1=No&mc_fee=0.50&notify_version=3.0&custom=test_user&payer_status=verified&business=brian@surfguitar101.com&quantity=1&verify_sign=Ai1PaTHIS-IS-FAKE-DATA-jB264AOjpiTa4vcsPCEavq-83oyIclHKI&payer_email=test_user@example.com&option_name1=List your name?&txn_id=TESTTXNID5815921V&payment_type=instant&last_name=Doe&receiver_email=brian@surfguitar101.com&payment_fee=0.50&receiver_id=FAKERECEIVERU&txn_type=web_accept&item_name=Donation for www.surfguitar101.com&mc_currency=USD&item_number=500&residence_country=AU&handling_amount=0.00&transaction_subject=test_user&payment_gross=5.00&shipping=0.00"""

# Data from a user that wanted to remain anonymous
TEST_POST_DATA_2 = """\
mc_gross=100.00&protection_eligibility=Ineligible&payer_id=FAKEPAYERID02&tax=0.00&payment_date=05:40:33 Jan 16, 2011 PST&payment_status=Completed&charset=windows-1252&first_name=John&option_selection1=No&mc_fee=3.20&notify_version=3.0&custom=test_user&payer_status=unverified&business=brian@surfguitar101.com&quantity=1&verify_sign=AIkKNFAKE-DATA-NOT-REALpqCSxA-E7Tm4rMGlUpNy6ym0.exBzfiyI&payer_email=test_user@example.com&option_name1=List your name?&txn_id=TESTTXNIDK548343A&payment_type=instant&last_name=Doe&receiver_email=brian@surfguitar101.com&payment_fee=3.20&receiver_id=FAKERECEIVERU&txn_type=web_accept&item_name=Donation for www.surfguitar101.com&mc_currency=USD&item_number=501&residence_country=US&handling_amount=0.00&transaction_subject=test_user&payment_gross=100.00&shipping=0.00"""


class DonationsIpnTestCase(TestCase):
    fixtures = ['badges']

    def test_ipn_post_1(self):
        """
        Test a simulated IPN post
        """
        user = User.objects.create_user('test_user', 'test_user@example.com',
                'password')
        user.save()

        args = urlparse.parse_qs(TEST_POST_DATA_1)
        response = self.client.post(reverse('donations-ipn'), args)

        self.assertEqual(response.status_code, 200)

        try:
            d = Donation.objects.get(pk=1)
        except Donation.DoesNotExist:
            self.fail("Donation object was not created")
        else:
            self.assertEqual(d.user, user)
            self.assertFalse(d.is_anonymous)
            self.assertFalse(d.test_ipn)
            self.assertEqual(d.txn_id, 'TESTTXNID5815921V')
            self.assertEqual(d.txn_type, 'web_accept')
            self.assertEqual(d.first_name, 'John')
            self.assertEqual(d.last_name, 'Doe')
            self.assertEqual(d.payer_email, 'test_user@example.com')
            self.assertEqual(d.payer_id, 'FAKEPAYERID01')
            self.assertEqual(d.mc_fee, Decimal('0.50'))
            self.assertEqual(d.mc_gross, Decimal('5.00'))
            self.assertEqual(d.memo, '')
            self.assertEqual(d.payer_status, 'verified')
            self.assertEqual(d.payment_date,
                    datetime.datetime(2011, 1, 21, 4, 14, 8))

            # user should have got a badge for donating
            p = user.profile
            badges = list(p.badges.all())
            self.assertEqual(len(badges), 1)
            if len(badges) == 1:
                self.assertEqual(badges[0].numeric_id, bio.badges.CONTRIBUTOR_PIN)

    def test_ipn_post_2(self):
        """
        Test a simulated IPN post
        """
        user = User.objects.create_user('test_user', 'test_user@example.com',
                'password')
        user.save()

        args = urlparse.parse_qs(TEST_POST_DATA_2)
        response = self.client.post(reverse('donations-ipn'), args)

        self.assertEqual(response.status_code, 200)

        try:
            d = Donation.objects.get(pk=1)
        except Donation.DoesNotExist:
            self.fail("Donation object was not created")
        else:
            self.assertEqual(d.user, user)
            self.assertTrue(d.is_anonymous)
            self.assertFalse(d.test_ipn)
            self.assertEqual(d.txn_id, 'TESTTXNIDK548343A')
            self.assertEqual(d.txn_type, 'web_accept')
            self.assertEqual(d.first_name, 'John')
            self.assertEqual(d.last_name, 'Doe')
            self.assertEqual(d.payer_email, 'test_user@example.com')
            self.assertEqual(d.payer_id, 'FAKEPAYERID02')
            self.assertEqual(d.mc_fee, Decimal('3.20'))
            self.assertEqual(d.mc_gross, Decimal('100.00'))
            self.assertEqual(d.memo, '')
            self.assertEqual(d.payer_status, 'unverified')
            self.assertEqual(d.payment_date,
                    datetime.datetime(2011, 1, 16, 5, 40, 33))

            # user should not have got a badge for donating
            p = user.profile
            self.assertEqual(p.badges.count(), 0)


class DonationsManagerTestCase(TestCase):
    fixtures = ['donations_test']

    def test_monthly_goal_pct(self):

        self.assertEqual(settings.DONATIONS_GOAL, Decimal('94.00'))
        pct = Donation.objects.monthly_goal_pct(year=2012, month=9)
        self.assertEqual(pct, 24)

    def test_monthly_goal_pct2(self):

        # Ensure we get 0 when there are no records

        Donation.objects.all().delete()
        pct = Donation.objects.monthly_goal_pct(year=2012, month=9)
        self.assertEqual(pct, 0)

    def test_monthly_stats(self):

        gross, net, donations = Donation.objects.monthly_stats(year=2012, month=9)
        self.assertEqual(gross, Decimal('25.00'))
        self.assertEqual(net, Decimal('23.47'))
        self.assertEqual(len(donations), 2)

    def test_monthly_stats2(self):

        # Ensure we get 0 when there are no records

        Donation.objects.all().delete()

        gross, net, donations = Donation.objects.monthly_stats(year=2012, month=9)
        self.assertEqual(gross, Decimal('0.00'))
        self.assertEqual(net, Decimal('0.00'))
        self.assertEqual(len(donations), 0)


# A complete, valid IPN payload for a *named* ($5) donation, as a dict so
# individual fields can be overridden per scenario. Mirrors the shape of a real
# Paypal "web_accept" completed-payment notification.
def valid_ipn(**overrides):
    data = {
        'mc_gross': '5.00',
        'mc_fee': '0.50',
        'payer_id': 'FAKEPAYERID01',
        'payment_date': '04:14:08 Jan 21, 2011 PST',
        'payment_status': 'Completed',
        'first_name': 'John',
        'last_name': 'Doe',
        'custom': 'test_user',
        'payer_status': 'verified',
        'business': 'brian@surfguitar101.com',
        'payer_email': 'test_user@example.com',
        'txn_id': 'TESTTXNID0001',
        'receiver_email': 'brian@surfguitar101.com',
        'txn_type': 'web_accept',
        'item_name': 'Donation for www.surfguitar101.com',
        'mc_currency': 'USD',
        'item_number': settings.DONATIONS_ITEM_NUM,
    }
    data.update(overrides)
    # Allow a field to be dropped entirely by passing it as None.
    return {k: v for k, v in data.items() if v is not None}


class IpnRejectionTestCase(TestCase):
    """
    Locks in the IPN handler's defensive branches: which malformed, unverified,
    or non-qualifying notifications must NOT create a Donation. The listener
    always answers Paypal with an empty 200, so these assert on the database, not
    the response code.
    """
    fixtures = ['badges']

    def setUp(self):
        User.objects.create_user('test_user', 'test_user@example.com', 'password')

    def post_ipn(self, **overrides):
        response = self.client.post(reverse('donations-ipn'), valid_ipn(**overrides))
        self.assertEqual(response.status_code, 200)
        return response

    def test_valid_ipn_is_saved(self):
        # Anchors the helper: an unmodified valid payload creates one donation.
        self.post_ipn()
        self.assertEqual(Donation.objects.count(), 1)

    @override_settings(DONATIONS_DEBUG_VERIFY_RESPONSE='INVALID')
    def test_unverified_ipn_is_ignored(self):
        self.post_ipn()
        self.assertEqual(Donation.objects.count(), 0)

    def test_non_completed_payment_is_ignored(self):
        self.post_ipn(payment_status='Pending')
        self.assertEqual(Donation.objects.count(), 0)

    def test_non_donation_item_number_is_ignored(self):
        self.post_ipn(item_number='999')
        self.assertEqual(Donation.objects.count(), 0)

    def test_missing_txn_id_is_rejected(self):
        self.post_ipn(txn_id=None)
        self.assertEqual(Donation.objects.count(), 0)

    def test_duplicate_txn_id_is_not_double_counted(self):
        self.post_ipn()
        self.post_ipn()   # identical txn_id
        self.assertEqual(Donation.objects.count(), 1)

    def test_wrong_business_email_is_rejected(self):
        self.post_ipn(business='scammer@example.com')
        self.assertEqual(Donation.objects.count(), 0)

    def test_wrong_txn_type_is_rejected(self):
        self.post_ipn(txn_type='send_money')
        self.assertEqual(Donation.objects.count(), 0)

    def test_missing_amounts_are_rejected(self):
        self.post_ipn(mc_gross=None)
        self.assertEqual(Donation.objects.count(), 0)

    def test_missing_payment_date_is_rejected(self):
        self.post_ipn(payment_date=None)
        self.assertEqual(Donation.objects.count(), 0)

    def test_invalid_payment_date_is_rejected(self):
        self.post_ipn(payment_date='not a date XYZ')
        self.assertEqual(Donation.objects.count(), 0)


class IpnEdgeCaseTestCase(TestCase):
    """Valid donations whose payer details fall outside the common case."""
    fixtures = ['badges']

    def post_ipn(self, **overrides):
        response = self.client.post(reverse('donations-ipn'), valid_ipn(**overrides))
        self.assertEqual(response.status_code, 200)
        return response

    def test_unknown_custom_user_saves_donation_without_user(self):
        # 'custom' names a user who doesn't exist -> donation still recorded,
        # just unlinked.
        self.post_ipn(custom='ghost')
        donation = Donation.objects.get()
        self.assertIsNone(donation.user)

    def test_test_ipn_flag_is_recorded(self):
        User.objects.create_user('test_user', 'test_user@example.com', 'password')
        self.post_ipn(test_ipn='1')
        donation = Donation.objects.get()
        self.assertTrue(donation.test_ipn)


class DonationsPageTestCase(TestCase):
    """The public-facing donations pages render."""

    def test_index_page_renders(self):
        response = self.client.get(reverse('donations-index'))
        self.assertEqual(response.status_code, 200)

    def test_thanks_page_renders(self):
        response = self.client.get(reverse('donations-thanks'))
        self.assertEqual(response.status_code, 200)
