"""
Tests for the donations application.
"""
from urllib.parse import parse_qs
from decimal import Decimal
from importlib import import_module
import datetime
from zoneinfo import ZoneInfo

import requests
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.apps import apps as global_apps
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from donations.models import Donation
from donations.views import verify_request, paypal_params, parse_payment_date
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

        args = parse_qs(TEST_POST_DATA_1)
        response = self.client.post(reverse('donations-ipn'), args)

        self.assertEqual(response.status_code, 200)

        try:
            d = Donation.objects.get()
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
            # The clock Paypal reported, in the zone Paypal reported it in.
            self.assertEqual(d.payment_date,
                    datetime.datetime(2011, 1, 21, 4, 14, 8,
                                      tzinfo=ZoneInfo('America/Los_Angeles')))

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

        args = parse_qs(TEST_POST_DATA_2)
        response = self.client.post(reverse('donations-ipn'), args)

        self.assertEqual(response.status_code, 200)

        try:
            d = Donation.objects.get()
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
                    datetime.datetime(2011, 1, 16, 5, 40, 33,
                                      tzinfo=ZoneInfo('America/Los_Angeles')))

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

    def test_custom_user_differing_case_is_linked(self):
        # 'custom' carries the username captured when the donation was made;
        # matching it case-sensitively would silently unlink real donations.
        user = User.objects.create_user('Test_User', 'test_user@example.com',
                                        'password')
        self.post_ipn(custom='test_user')
        donation = Donation.objects.get()
        self.assertEqual(donation.user, user)

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


# The DONATIONS_DEBUG_VERIFY_RESPONSE=None override disables the test settings'
# short-circuit so these exercise the real requests-based verify path (which
# replaced urllib2). requests.post is mocked so no network call happens.
@override_settings(DONATIONS_DEBUG_VERIFY_RESPONSE=None)
class VerifyRequestTestCase(TestCase):
    """The PayPal IPN postback verification (donations.views.verify_request)."""

    @patch('donations.views.requests.post')
    def test_posts_payload_back_to_paypal_and_returns_text(self, post_mock):
        post_mock.return_value = Mock(text='VERIFIED')

        result = verify_request('cmd=_notify-validate&txn_id=X')

        self.assertEqual(result, 'VERIFIED')
        post_mock.assert_called_once()
        args, kwargs = post_mock.call_args
        # posts to the configured Paypal URL, echoing the payload verbatim as
        # a form-urlencoded body.
        self.assertEqual(args[0], paypal_params()[0])
        self.assertEqual(kwargs['data'], 'cmd=_notify-validate&txn_id=X')
        self.assertEqual(kwargs['headers']['Content-type'],
                         'application/x-www-form-urlencoded')
        self.assertIn('timeout', kwargs)

    @patch('donations.views.requests.post')
    def test_returns_none_on_request_exception(self, post_mock):
        post_mock.side_effect = requests.RequestException('boom')
        self.assertIsNone(verify_request('cmd=_notify-validate&txn_id=X'))

    @patch('donations.views.requests.post')
    def test_http_error_status_yields_none(self, post_mock):
        # raise_for_status() escalates a 500 to a RequestException -> None,
        # matching the old urllib2 behavior of raising on non-2xx.
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError('500')
        post_mock.return_value = response
        self.assertIsNone(verify_request('cmd=_notify-validate'))


class MonthBoundaryTestCase(TestCase):
    """
    A donation made in the evening on the last day of a month is already the
    1st in UTC. Which month it is reported under therefore depends on the
    timezone the query reads it in, and nothing about getting that wrong is
    loud: the totals are simply short by one donation.
    """
    def setUp(self):
        # 7pm Chicago on the last day of January; 01:00 UTC on February 1st.
        self.chicago = ZoneInfo('America/Chicago')
        self.donation = Donation.objects.create(
                txn_id='boundary-1', txn_type='web_accept',
                mc_gross=Decimal('20.00'), mc_fee=Decimal('1.00'),
                payment_date=datetime.datetime(2026, 1, 31, 19, 0,
                                               tzinfo=self.chicago))

    def test_the_donation_is_stored_in_the_next_utc_month(self):
        """Guard the premise: if this row is not actually across the boundary,
        every other test here passes without proving anything."""
        stored = self.donation.payment_date.astimezone(datetime.timezone.utc)
        self.assertEqual((stored.year, stored.month, stored.day), (2026, 2, 1))

    def test_monthly_stats_files_it_under_january(self):
        gross, net, donations = Donation.objects.monthly_stats(year=2026,
                                                               month=1)
        self.assertEqual(gross, Decimal('20.00'))
        self.assertEqual(len(donations), 1)

    def test_monthly_stats_does_not_file_it_under_february(self):
        gross, net, donations = Donation.objects.monthly_stats(year=2026,
                                                               month=2)
        self.assertEqual(len(donations), 0)

    def test_the_month_does_not_follow_an_activated_timezone(self):
        """The rollup is about the site's calendar, not the viewer's. With a
        per-user timezone activated -- which is one obvious way to render
        times, and what the middleware approach would have done -- an
        unpinned lookup silently reports this donation in February."""
        for name in ['UTC', 'US/Pacific', 'Australia/Sydney']:
            with self.subTest(tz=name), timezone.override(name):
                _, _, donations = Donation.objects.monthly_stats(year=2026,
                                                                 month=1)
                self.assertEqual(len(donations), 1)

    def test_monthly_goal_pct_uses_the_same_month(self):
        with timezone.override('UTC'):
            pct = Donation.objects.monthly_goal_pct(year=2026, month=1)
        self.assertEqual(pct, 20)   # (20.00 - 1.00) / 94.00


UTC = datetime.timezone.utc

# The backfill migration, imported by path because its module name begins with a
# digit. Only its pure helper and its constants are used here; the migration
# itself is run by the test runner like any other.
backfill = import_module(
    'donations.migrations.0002_payment_date_pacific_backfill')


class PaymentDateParseTestCase(TestCase):
    """
    Paypal reports payment_date as a Pacific wall clock with the zone as a
    trailing abbreviation. The abbreviation says which side of a DST change the
    reading is on; it is not itself decodable, since PST alone is also
    Philippine Standard Time, sixteen hours the other way. So these assert that
    the two abbreviations Paypal sends are honoured and that everything else is
    refused rather than guessed at.
    """

    def test_pst_is_stored_at_the_instant_paypal_reported(self):
        parsed = parse_payment_date('04:14:08 Jan 21, 2011 PST')
        self.assertEqual(parsed.astimezone(UTC),
                         datetime.datetime(2011, 1, 21, 12, 14, 8, tzinfo=UTC))

    def test_pst_is_not_the_old_chicago_reading(self):
        """Guard the premise. The defect stamped this same clock with
        TIME_ZONE, two hours ahead of Pacific -- if that value ever passes
        here, the test above is asserting about the wrong instant."""
        parsed = parse_payment_date('04:14:08 Jan 21, 2011 PST')
        self.assertNotEqual(parsed.astimezone(UTC),
                            datetime.datetime(2011, 1, 21, 10, 14, 8,
                                              tzinfo=UTC))

    def test_pdt_takes_the_daylight_offset(self):
        """A summer date must come out at -07:00. The zone is mapped rather
        than the offset, so this is zoneinfo reading the date, not the
        abbreviation being trusted for an offset."""
        parsed = parse_payment_date('10:00:00 Jul 15, 2011 PDT')
        self.assertEqual(parsed.utcoffset(), datetime.timedelta(hours=-7))
        self.assertEqual(parsed.astimezone(UTC),
                         datetime.datetime(2011, 7, 15, 17, 0, 0, tzinfo=UTC))

    def test_the_ambiguous_hour_is_resolved_by_the_abbreviation(self):
        """On the morning the clocks go back, 01:30 happens twice and the wall
        clock cannot say which pass it is. The abbreviation can, and it is the
        only thing that can."""
        pdt = parse_payment_date('01:30:00 Nov 2, 2025 PDT')
        pst = parse_payment_date('01:30:00 Nov 2, 2025 PST')
        self.assertEqual(pdt.astimezone(UTC),
                         datetime.datetime(2025, 11, 2, 8, 30, tzinfo=UTC))
        self.assertEqual(pst.astimezone(UTC),
                         datetime.datetime(2025, 11, 2, 9, 30, tzinfo=UTC))

    def test_an_unknown_zone_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            parse_payment_date('04:14:08 Jan 21, 2011 EST')
        self.assertIn('timezone "EST"', str(caught.exception))

    def test_the_abbreviation_length_is_not_assumed(self):
        """The old parse chopped a fixed four characters off the end. A
        four-letter zone must be reported by its whole name -- naming 'AKD' or
        'KDT' would mean the split had cut into the token, and the same cut
        applied to a shorter one would eat the year."""
        with self.assertRaises(ValueError) as caught:
            parse_payment_date('04:14:08 Jan 21, 2011 AKDT')
        # Named as the zone, not merely present: the message echoes the whole
        # input too, so a looser assertion would be satisfied by that echo
        # while the split quietly cut the token down to "KDT".
        self.assertIn('timezone "AKDT"', str(caught.exception))

    def test_a_date_with_no_zone_is_refused(self):
        with self.assertRaises(ValueError):
            parse_payment_date('04:14:08 Jan 21, 2011')

    def test_junk_is_refused(self):
        with self.assertRaises(ValueError):
            parse_payment_date('not a date XYZ')


@override_settings(ADMINS=[('Admin', 'admin@example.com')])
class IpnPaymentDateTestCase(TestCase):
    """The parse as the listener uses it: what reaches the database, and what
    happens when a zone we do not map arrives."""
    fixtures = ['badges']

    def setUp(self):
        User.objects.create_user('test_user', 'test_user@example.com',
                                 'password')

    def post_ipn(self, **overrides):
        response = self.client.post(reverse('donations-ipn'),
                                    valid_ipn(**overrides))
        self.assertEqual(response.status_code, 200)
        return response

    def test_a_donation_is_stored_at_the_reported_instant(self):
        self.post_ipn()
        donation = Donation.objects.get()
        self.assertEqual(donation.payment_date.astimezone(UTC),
                         datetime.datetime(2011, 1, 21, 12, 14, 8, tzinfo=UTC))

    def test_an_unknown_zone_creates_no_donation(self):
        self.post_ipn(payment_date='04:14:08 Jan 21, 2011 EST')
        self.assertEqual(Donation.objects.count(), 0)

    def test_an_unknown_zone_reaches_a_person(self):
        """The listener answers Paypal 200 whatever happens, so Paypal never
        retries and a refusal is a donation record lost for good. A log line
        alone would be found only by someone already looking."""
        self.post_ipn(payment_date='04:14:08 Jan 21, 2011 EST')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('EST', mail.outbox[0].body)


class PaymentDateBackfillTestCase(TestCase):
    """
    The backfill helper. Every donation on file was recorded by the old parse
    and is two hours early; the boundary is what keeps the correction off rows
    written after the fixed parse went live.
    """

    def setUp(self):
        self.boundary = timezone.now()
        self.before = self._donation('before', self.boundary
                                     - datetime.timedelta(days=1))
        self.after = self._donation('after', self.boundary
                                    + datetime.timedelta(days=1))

    def _donation(self, txn_id, payment_date):
        return Donation.objects.create(txn_id=txn_id, txn_type='web_accept',
                                       mc_gross=Decimal('10.00'),
                                       mc_fee=Decimal('1.00'),
                                       payment_date=payment_date)

    def test_a_row_before_the_boundary_moves_two_hours(self):
        original = self.before.payment_date
        backfill.shift_donations(Donation, self.boundary, backfill.SHIFT)
        self.before.refresh_from_db()
        self.assertEqual(self.before.payment_date - original,
                         datetime.timedelta(hours=2))

    def test_a_row_after_the_boundary_does_not_move(self):
        original = self.after.payment_date
        backfill.shift_donations(Donation, self.boundary, backfill.SHIFT)
        self.after.refresh_from_db()
        self.assertEqual(self.after.payment_date, original)

    def test_the_shift_is_exactly_reversible(self):
        original = self.before.payment_date
        backfill.shift_donations(Donation, self.boundary, backfill.SHIFT)
        backfill.shift_donations(Donation, self.boundary, -backfill.SHIFT)
        self.before.refresh_from_db()
        self.assertEqual(self.before.payment_date, original)

    def test_reversing_leaves_a_later_row_alone(self):
        """A rollback after the site is live is the case this guards: rows
        written by the corrected parse in the meantime are already right, and
        an unbounded reverse would break them."""
        original = self.after.payment_date
        backfill.shift_donations(Donation, self.boundary, -backfill.SHIFT)
        self.after.refresh_from_db()
        self.assertEqual(self.after.payment_date, original)


class BackfillAppliedOnceTestCase(TestCase):
    """
    Nothing in a row says whether it has been corrected, so the migration must
    not run twice. That guarantee comes from Django's applied-migrations record
    rather than from anything in the helper.
    """

    def test_the_migration_is_recorded_as_applied(self):
        applied = MigrationRecorder(connection).applied_migrations()
        self.assertIn(('donations',
                       '0002_payment_date_pacific_backfill'), applied)

    def test_a_second_migrate_moves_nothing(self):
        donation = Donation.objects.create(
                txn_id='second-migrate', txn_type='web_accept',
                mc_gross=Decimal('10.00'), mc_fee=Decimal('1.00'),
                payment_date=timezone.now() - datetime.timedelta(days=1))
        original = donation.payment_date
        call_command('migrate', 'donations', verbosity=0)
        donation.refresh_from_db()
        self.assertEqual(donation.payment_date, original)


class BackfillReverseTestCase(TestCase):
    """
    The reverse takes its boundary from Django's record of when the forward
    ran, not from the clock at the moment of the rollback. The difference only
    shows once the site has been live in between -- which is exactly when a
    rollback happens.
    """

    def setUp(self):
        self.applied = MigrationRecorder(connection).migration_qs.get(
                app='donations', name=backfill.NAME).applied

    def _donation(self, txn_id, payment_date):
        return Donation.objects.create(txn_id=txn_id, txn_type='web_accept',
                                       mc_gross=Decimal('10.00'),
                                       mc_fee=Decimal('1.00'),
                                       payment_date=payment_date)

    def _reverse(self):
        with connection.schema_editor() as schema_editor:
            backfill.back_to_chicago(global_apps, schema_editor)

    def test_a_row_the_forward_corrected_goes_back(self):
        donation = self._donation('pre-applied', self.applied
                                  - datetime.timedelta(days=1))
        original = donation.payment_date
        self._reverse()
        donation.refresh_from_db()
        self.assertEqual(original - donation.payment_date,
                         datetime.timedelta(hours=2))

    def test_a_donation_taken_after_the_forward_is_left_alone(self):
        """Recorded by the corrected parse while the site was live, so it is
        already right. Reversing against the current clock instead of the
        recorded one would walk it back two hours."""
        donation = self._donation('post-applied', self.applied
                                  + datetime.timedelta(seconds=1))
        original = donation.payment_date
        self._reverse()
        donation.refresh_from_db()
        self.assertEqual(donation.payment_date, original)
