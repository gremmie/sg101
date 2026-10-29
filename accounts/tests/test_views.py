"""
View tests for the accounts application.

"""
import datetime
import logging
import re
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.db import connection
from django.conf import settings
from django.utils import timezone

from accounts.models import EMAIL_CHANGE_EXPIRATION
from accounts.models import PendingEmailChange
from accounts.models import PendingUser
from accounts.models import IllegalUsername
from accounts.models import IllegalEmail
from accounts.utils import make_confirmation_token
from antispam.turnstile import TurnstileOutcome, TurnstileResult



def suspend_email_uniqueness():
    """Drop the LOWER(email) unique index for the rest of this transaction.

    For tests that have to build two accounts on one address to prove the code
    handling that state still works. A TestCase rolls back, which restores the
    index; nothing outside the test sees it gone.

    """
    with connection.cursor() as cursor:
        cursor.execute('DROP INDEX IF EXISTS auth_user_email_lower_uniq')


class RegistrationTest(TestCase):

    def setUp(self):
        u = User.objects.create_user('existing_user', 'existing_user@example.com', 'pw')
        u.save()

        # A second account on the same address used to sit here, so that the
        # duplicate check was exercised against more than one match. The unique
        # index on LOWER(email) forbids that row now, and the tests below never
        # needed it: one existing account is enough to be rejected by.

        PendingUser.objects.create(username='pending_user',
            email='pending_user@example.com',
            password='pw',
            date_joined=timezone.now(),
            key='key')

        IllegalUsername.objects.create(username='illegalusername')
        IllegalEmail.objects.create(email='illegal@example.com')

        self.post_vals = {
            'username': 'a_new_user',
            'email': 'test@example.com',
            'password1': 'my_password',
            'password2': 'my_password',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question': '',
            'cf-turnstile-response': 'a-token',
        }

        # Every POST to the register view reaches the verification helper, so
        # it is mocked here rather than in twenty tests; what a test varies is
        # the outcome it returns.
        self.turnstile = patch('accounts.forms.turnstile.verify')
        self.verify = self.turnstile.start()
        self.addCleanup(self.turnstile.stop)
        self.verify.return_value = TurnstileResult(TurnstileOutcome.PASSED)

    def test_get_view(self):
        """
        Test a simple get of the registration view

        """
        response = self.client.get(reverse('accounts-register'))
        self.assertEqual(response.status_code, 200)

    def test_widget_is_rendered(self):
        """
        The view's context key and the template's must agree, and only a
        rendered page can say they do.

        """
        response = self.client.get(reverse('accounts-register'))

        self.assertContains(response, 'cf-turnstile')
        self.assertContains(response, settings.TURNSTILE_SITE_KEY)
        self.assertContains(response,
                            'challenges.cloudflare.com/turnstile/v0/api.js')

    def test_the_old_routes_are_gone(self):
        """
        The two-stage code flow left three URLs behind it.

        """
        for url in ['/accounts/register/1/', '/accounts/register/2/',
                    '/accounts/register/code/']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, msg=url)

    def test_the_agreement_labels_name_their_own_boxes(self):
        """
        A label whose `for` does not resolve to an input is inert when
        clicked, and the page renders identically either way -- which is how
        three required checkboxes went a decade without working labels.

        """
        response = self.client.get(reverse('accounts-register'))
        html = response.content.decode()

        for field in ['agree_age', 'agree_tos', 'agree_privacy']:
            self.assertRegex(
                    html,
                    r'id="id_%s"\s*>\s*<label for="id_%s"' % (field, field),
                    msg='%s: the label does not name the box beside it' % field)

    def test_a_rejected_token_blocks_registration(self):
        """
        A rejected challenge stops stage one before anything is written.

        """
        self.verify.return_value = TurnstileResult(
                TurnstileOutcome.REJECTED, ('invalid-input-response',))

        response = self.client.post(reverse('accounts-register'),
                                    self.post_vals)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            PendingUser.objects.filter(username='a_new_user').exists())
        self.assertIn("couldn't verify",
                      response.context['form'].non_field_errors()[0])

    def test_a_missing_token_costs_no_request(self):
        """
        A submission that never loaded the widget must not reach Cloudflare.

        The class-wide mock stands down for this one: what is under test is
        that nothing goes on the wire, which a mocked verify() cannot show.

        """
        del self.post_vals['cf-turnstile-response']
        self.turnstile.stop()
        try:
            with patch('antispam.turnstile.requests.post') as request_post:
                response = self.client.post(reverse('accounts-register'),
                                            self.post_vals)
        finally:
            self.turnstile.start()

        request_post.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            PendingUser.objects.filter(username='a_new_user').exists())
        self.assertIn('Please verify',
                      response.context['form'].non_field_errors()[0])

    def test_an_outage_fails_open(self):
        """
        An outage must not take registration down with it.

        The other layers still apply and the helper has already logged the
        skipped check at WARNING, which is the only record that the challenge
        did not actually happen.

        """
        self.verify.return_value = TurnstileResult(TurnstileOutcome.UNAVAILABLE)

        response = self.client.post(reverse('accounts-register'),
                                    self.post_vals)

        self.assertRedirects(response, reverse('accounts-register_thanks'))
        self.assertTrue(
                PendingUser.objects.filter(username='a_new_user').exists())

    def test_a_rejection_is_logged_for_the_instrument(self):
        """
        The auth log is the only measure this flow has, and a failure mode
        invisible to it would be a blind spot in that measurement.

        """
        self.verify.return_value = TurnstileResult(
                TurnstileOutcome.REJECTED, ('invalid-input-response',))

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('auth', level='ERROR') as logged:
            self.client.post(reverse('accounts-register'), self.post_vals)

        self.assertTrue(
                any('Accounts/registration [127.0.0.1]:' in line and
                    'robot' in line for line in logged.output),
                msg='the rejection is not greppable in the usual shape')

    def test_existing_user(self):
        """
        Ensure we can't register with an existing username.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'existing_user',
            'email': 'test@example.com',
            'password1': 'my_password',
            'password2': 'my_password',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question': '',
            'cf-turnstile-response': 'a-token',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that username already exists')

    def test_existing_user_differing_case(self):
        """
        Ensure we can't register a case variant of an existing username.

        MySQL's case-insensitive collations gave us this for free; on any
        case-sensitive engine it takes an explicit __iexact lookup.

        """
        self.post_vals['username'] = 'EXISTING_USER'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that username already exists')

    def test_pending_user(self):
        """
        Ensure we can't register with a pending username.

        """
        self.post_vals['username'] = 'pending_user'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A pending user with that username already exists')

    def test_pending_user_differing_case(self):
        """
        Ensure we can't register a case variant of a pending username.

        """
        self.post_vals['username'] = 'PENDING_USER'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A pending user with that username already exists')

    def test_illegal_username(self):
        """
        Ensure we can't register with a banned username.

        """
        self.post_vals['username'] = 'illegalusername'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That username is not allowed')

    def test_illegal_username_differing_case(self):
        """
        Ensure the username blocklist can't be evaded by changing case.

        This is an abuse control, so a silent case-sensitivity change here
        matters more than the duplicate-account checks around it.

        """
        self.post_vals['username'] = 'IllegalUsername'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That username is not allowed')

    def test_duplicate_existing_email(self):
        """
        Ensure we can't register with a duplicate email address.

        """
        self.post_vals['email'] = 'existing_user@example.com'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that email address already exists')

    def test_duplicate_existing_email_differing_case(self):
        """
        Ensure we can't register a case variant of an existing email address.

        """
        self.post_vals['email'] = 'Existing_User@Example.com'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that email address already exists')

    def test_duplicate_pending_email(self):
        """
        Ensure we can't register with a duplicate email address.

        """
        self.post_vals['email'] = 'pending_user@example.com'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A pending user with that email address already exists')

    def test_duplicate_pending_email_differing_case(self):
        """
        Ensure we can't register a case variant of a pending email address.

        """
        self.post_vals['email'] = 'Pending_User@Example.com'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A pending user with that email address already exists')

    def test_illegal_email(self):
        """
        Ensure we can't register with a banned email address.

        """
        self.post_vals['email'] = 'illegal@example.com'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That email address is not allowed')

    def test_illegal_email_differing_case(self):
        """
        Ensure the email blocklist can't be evaded by changing case.

        """
        self.post_vals['email'] = 'Illegal@Example.com'
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That email address is not allowed')

    def test_confirm_registration_differing_case(self):
        """
        Ensure a confirmation link resolves a case variant of the username.

        The emailed link carries the username as stored, so this guards
        hand-typed and mangled links rather than the nominal path.

        """
        pending = PendingUser.objects.create(username='MixedCaseUser',
            email='mixedcase@example.com',
            password='pw',
            date_joined=timezone.now(),
            key='a' * 20)

        response = self.client.get(reverse('accounts-register_confirm',
                                           kwargs={'username': 'mixedcaseuser',
                                                   'key': pending.key}))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            PendingUser.objects.filter(username='MixedCaseUser').exists(),
            msg='the pending user survived confirmation')
        self.assertTrue(User.objects.filter(username='MixedCaseUser').exists(),
                        msg='the real user was not created')

    def test_legacy_short_key_still_confirms(self):
        """
        A key issued before the move to secrets.token_urlsafe must still work.

        Registration keys were 20 characters of hex; the column and the URL
        pattern were both sized for exactly that. Widening them must not strand
        a link already sitting in somebody's inbox -- the expiry window is a
        day, so such links exist right through the deploy.

        """
        pending = PendingUser.objects.create(username='oldkeyuser',
            email='oldkey@example.com',
            password='pw',
            date_joined=timezone.now(),
            key='0123456789abcdef0123')

        response = self.client.get(reverse('accounts-register_confirm',
                                           kwargs={'username': 'oldkeyuser',
                                                   'key': pending.key}))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='oldkeyuser').exists(),
                        msg='a legacy 20-character key was refused')

    def test_wrong_key_is_refused(self):
        """
        Confirmation with the wrong key creates no user.

        This pins the behaviour, not the mechanism: it passes equally under a
        plain != comparison, because both reject a wrong key. compare_digest's
        property is timing, which a functional test cannot observe. What this
        does catch is the comparison being dropped or inverted.

        """
        pending = PendingUser.objects.create(username='wrongkeyuser',
            email='wrongkey@example.com',
            password='pw',
            date_joined=timezone.now(),
            key=make_confirmation_token())

        wrong = make_confirmation_token()
        self.assertNotEqual(wrong, pending.key)

        response = self.client.get(reverse('accounts-register_confirm',
                                           kwargs={'username': 'wrongkeyuser',
                                                   'key': wrong}))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='wrongkeyuser').exists(),
                         msg='a wrong key created the user anyway')
        self.assertTrue(
            PendingUser.objects.filter(username='wrongkeyuser').exists(),
            msg='the pending user was consumed by a failed confirmation')

    def test_password_match(self):
        """
        Ensure the passwords match.

        """
        self.post_vals['password2'] = "doesn't match"
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn&#x27;t match")

    def test_the_honeypot_is_caught_and_logged(self):
        """
        Ensure our honeypot question check works.

        A passing challenge must not excuse a filled honeypot: it and the
        widget are the two remaining layers and they are additive.

        Both log lines are asserted, not just the CRITICAL one. A filled
        honeypot is deliberately logged twice, and the pair is what lets a
        count of honeypot hits be checked against a count of registration
        failures; a silent drop of either line would leave both counts looking
        healthy while disagreeing.

        """
        self.post_vals['question'] = 'non blank'

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('auth', level='ERROR') as logged:
            response = self.client.post(reverse('accounts-register'),
                                        self.post_vals)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            PendingUser.objects.filter(username='a_new_user').exists())
        self.assertTrue(
                any('Honeypot filled [127.0.0.1]' in line
                    for line in logged.output),
                msg='the honeypot hit is not greppable in the counted shape')
        self.assertTrue(
                any('Wrong answer' in line for line in logged.output),
                msg='the paired failure line is missing')

    def test_success(self):
        """
        Ensure we can successfully register.

        """
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('email', level='INFO') as logged:
            response = self.client.post(reverse('accounts-register'),
                                        self.post_vals)

        self.assertRedirects(response, reverse('accounts-register_thanks'))
        self.assertIn('category=registration', logged.output[0])

        # The ip the form was handed, not a second look at the request.
        self.verify.assert_called_once_with('a-token', '127.0.0.1',
                                            source='registration')

        try:
            pending = PendingUser.objects.get(username='a_new_user')
        except PendingUser.DoesNotExist:
            self.fail("PendingUser was not created")

        self.assertEqual(pending.email, 'test@example.com')
        self.assertTrue(timezone.now() - pending.date_joined <
                datetime.timedelta(minutes=1))
        self.assertTrue(check_password('my_password', pending.password))

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertTrue(msg.subject.startswith('Registration Confirmation'))
        self.assertTrue(len(msg.to) == 1 and msg.to[0] == pending.email)
        msg_text = msg.message().as_string()

        activation_link = 'http://example.com%s' % (
                reverse('accounts-register_confirm',
                        kwargs={'username': pending.username,
                                'key': pending.key}))
        self.assertTrue(activation_link in msg_text)

        # Vist confirm link
        response = self.client.get(reverse('accounts-register_confirm',
                                           kwargs={'username': pending.username,
                                                   'key': pending.key}))
        self.assertEqual(response.status_code, 200)

        try:
            PendingUser.objects.get(username='a_new_user')
        except PendingUser.DoesNotExist:
            pass
        else:
            self.fail("PendingUser was not deleted upon confirmation")

        user = User.objects.get(username=pending.username)
        self.assertEqual(user.email, pending.email)
        now = timezone.now()
        delta = datetime.timedelta(seconds=10)
        self.assertTrue(now - user.last_login < delta)
        self.assertTrue(now - user.date_joined < delta)
        self.assertEqual(user.password, pending.password)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)

    def test_the_success_line_keeps_its_shape(self):
        """
        The 'conf. email sent' line is the success signal the registration
        measurements are counted from, so its shape is load-bearing rather
        than cosmetic.

        """
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('auth', level='INFO') as logged:
            self.client.post(reverse('accounts-register'), self.post_vals)

        self.assertTrue(
                any('Accounts/registration conf. email sent to '
                    'test@example.com for user a_new_user; IP = 127.0.0.1'
                    in line for line in logged.output),
                msg='the success line is not greppable in the recorded shape')


class ForgotUsernameTest(TestCase):

    def setUp(self):
        u = User.objects.create_user('existing_user', 'existing_user@example.com', 'pw')
        u.save()

    def test_get_query_view(self):
        """Test a simple get of the username query view"""
        response = self.client.get(reverse('accounts-username_query'))
        self.assertEqual(response.status_code, 200)

    def test_get_username_sent_view(self):
        """Test a simple get of the username sent view"""
        response = self.client.get(reverse('accounts-username_sent'))
        self.assertEqual(response.status_code, 200)

    def test_invalid_email(self):
        """Test form submittal of unknown email address."""
        response = self.client.post(reverse('accounts-username_query'), {
            'email': 'bad_address@example.com',
            },
            follow=True)

        self.assertRedirects(response, reverse('accounts-username_sent'))

        self.assertEqual(len(mail.outbox), 0)

    def test_the_send_is_categorized(self):
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('email', level='INFO') as logged:
            self.client.post(reverse('accounts-username_query'), {
                'email': 'existing_user@example.com',
                }, follow=True)

        self.assertIn('category=forgot_username', logged.output[0])

    def test_valid_email(self):
        """Test form submittal of valid email address."""
        response = self.client.post(reverse('accounts-username_query'), {
            'email': 'existing_user@example.com',
            },
            follow=True)

        self.assertRedirects(response, reverse('accounts-username_sent'))

        self.assertEqual(len(mail.outbox), 1)
        if len(mail.outbox):
            self.assertTrue(mail.outbox[0].subject.startswith('Forgotten username'))
            self.assertIn('The requested username is existing_user',
                          mail.outbox[0].body)

    def test_valid_email_differing_case(self):
        """Test form submittal of a valid email address in another case."""
        response = self.client.post(reverse('accounts-username_query'), {
            'email': 'Existing_User@Example.com',
            },
            follow=True)

        self.assertRedirects(response, reverse('accounts-username_sent'))

        self.assertEqual(len(mail.outbox), 1)
        if len(mail.outbox):
            self.assertTrue(mail.outbox[0].subject.startswith('Forgotten username'))

    def test_email_shared_by_two_accounts(self):
        """Two accounts on one address get one email listing both usernames.

        No address in this database is held twice any more -- the unique index
        on LOWER(email) forbids it, and the accounts that were sharing one have
        been cleared. The lookup still refuses to assume a single match, and
        this still tests it, because the state is reachable by other routes: a
        restored backup from before the index, and MySQL, which does not get the
        index at all. It was a 500 before the lookup stopped calling get().

        The index is dropped inside this test's transaction and comes back with
        the rollback.

        """
        suspend_email_uniqueness()
        u = User.objects.create_user('second_user', 'existing_user@example.com',
                                     'pw')
        u.save()

        response = self.client.post(reverse('accounts-username_query'), {
            'email': 'existing_user@example.com',
            },
            follow=True)

        self.assertRedirects(response, reverse('accounts-username_sent'))
        self.assertEqual(len(mail.outbox), 1)

        body = mail.outbox[0].body
        self.assertIn('existing_user', body)
        self.assertIn('second_user', body)
        self.assertIn('2 accounts', body)


class ForgotEmailTest(TestCase):
    """Because we use a custom URL its important to test this. This got broken
    in Django 1.6 when the URL pattern changed.

    """

    def setUp(self):
        u = User.objects.create_user('user1', 'user1@example.com', 'pw')
        u.save()

    def test_nominal_case(self):
        """Test a full forgot password scenario."""

        # GET password reset page
        response = self.client.get(reverse('accounts-password_reset'))
        self.assertEqual(response.status_code, 200)

        # POST email address
        args = {'email': 'user1@example.com'}
        response = self.client.post(reverse('accounts-password_reset'), args,
                follow=True)
        self.assertRedirects(response, reverse('accounts-password_reset_sent'))

        # Ensure the email was sent
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertTrue(msg.subject.startswith('Password reset'))
        self.assertTrue(len(msg.to) == 1 and msg.to[0] == 'user1@example.com')
        msg_text = msg.message().as_string()
        m = re.search(r'http://example.com/accounts/password/reset/confirm/'
            r'(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9a-z]+-\w+)/',
            msg_text)
        self.assertIsNotNone(m, "no reset link in the email")
        uidb64, token = m.group('uidb64'), m.group('token')

        # Visiting the emailed link stashes the token in the session and
        # redirects to the same route with a 'set-password' placeholder; the
        # form is served from there.
        confirm_url = reverse('accounts-password_reset_confirm',
                              kwargs={'uidb64': uidb64, 'token': token})
        set_password_url = reverse('accounts-password_reset_confirm',
                                   kwargs={'uidb64': uidb64,
                                           'token': 'set-password'})
        response = self.client.get(confirm_url)
        self.assertRedirects(response, set_password_url)

        response = self.client.get(set_password_url)
        self.assertEqual(response.status_code, 200)

        # POST new password
        args = {'new_password1': 'pw2', 'new_password2': 'pw2'}
        response = self.client.post(set_password_url, args, follow=True)
        self.assertRedirects(response,
                reverse('accounts-password_reset_success'))
        self.assertEqual(response.status_code, 200)

        # Check new password
        u = User.objects.get(username='user1')
        self.assertTrue(check_password('pw2', u.password))

    def test_differing_case_email(self):
        """A reset request in another case still finds the account.

        Django's own PasswordResetForm.get_users() already looks the address up
        with __iexact, so this holds on a case-sensitive engine without any
        change on our side. Pinned so a later rung can't quietly drop it.

        """
        args = {'email': 'User1@Example.com'}
        response = self.client.post(reverse('accounts-password_reset'), args,
                follow=True)
        self.assertRedirects(response, reverse('accounts-password_reset_sent'))

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].subject.startswith('Password reset'))


class PasswordResetRoutingTest(TestCase):
    """Password reset must go through the site's mail wrapper.

    Django's stock PasswordResetView sends the message itself, inline in the
    request: no Celery, no retry, no send logging, and a round trip to the mail
    provider while the user waits. accounts.forms.SitePasswordResetForm is what
    redirects it, and these tests are what notice if the form_class is ever
    dropped from the URLconf -- at which point everything still appears to work,
    because the mail is still sent.
    """

    def setUp(self):
        u = User.objects.create_user('user1', 'user1@example.com', 'pw')
        u.save()

    @patch('core.functions.send_mail')
    def test_reset_email_goes_through_the_site_wrapper(self, send_mail_mock):
        args = {'email': 'user1@example.com'}
        response = self.client.post(reverse('accounts-password_reset'), args,
                                    follow=True)

        self.assertRedirects(response, reverse('accounts-password_reset_sent'))
        self.assertEqual(send_mail_mock.call_count, 1)
        call_args = send_mail_mock.call_args[0]
        subject, body, from_email, recipients = call_args
        self.assertEqual(recipients, ['user1@example.com'])
        self.assertEqual(from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertTrue(subject.startswith('Password reset'))
        self.assertIn('/accounts/password/reset/confirm/', body)

    @patch('core.functions.send_mail')
    def test_subject_has_no_newline(self, send_mail_mock):
        # The subject template ends in a newline and a newline in a subject
        # header is an injection, so the join that strips it must stay.
        self.client.post(reverse('accounts-password_reset'),
                         {'email': 'user1@example.com'}, follow=True)

        subject = send_mail_mock.call_args[0][0]
        self.assertNotIn('\n', subject)
        self.assertNotIn('\r', subject)

    @patch('core.functions.send_mail')
    def test_from_email_is_never_the_string_none(self, send_mail_mock):
        # The view leaves from_email as None and Django relies on
        # EmailMultiAlternatives to fall back. The wrapper does not.
        self.client.post(reverse('accounts-password_reset'),
                         {'email': 'user1@example.com'}, follow=True)

        from_email = send_mail_mock.call_args[0][2]
        self.assertIsNotNone(from_email)
        self.assertNotEqual(from_email, 'None')

    def test_the_send_is_categorized(self):
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('email', level='INFO') as logged:
            self.client.post(reverse('accounts-password_reset'),
                             {'email': 'user1@example.com'}, follow=True)

        self.assertIn('category=password_reset', logged.output[0])

    @patch('core.functions.send_mail')
    def test_a_failing_send_does_not_500_the_reset_page(self, send_mail_mock):
        # Django swallows send failures here so a broken mail path cannot fail
        # the page, which would also disclose whether an address has an
        # account. Routing through Celery moves the risk to the broker --
        # delay() raises if Redis is unreachable -- so the guarantee has to be
        # kept deliberately rather than inherited.
        send_mail_mock.side_effect = OSError('broker unreachable')

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('email', level='ERROR') as logged:
            response = self.client.post(reverse('accounts-password_reset'),
                                        {'email': 'user1@example.com'},
                                        follow=True)

        self.assertRedirects(response, reverse('accounts-password_reset_sent'))
        self.assertEqual(len(logged.records), 1)

    @patch('core.functions.send_mail')
    def test_unknown_address_is_indistinguishable_from_a_known_one(
            self, send_mail_mock):
        """An address with no account must produce the same response.

        This is a user-enumeration guard, not a routing test, and it does not
        discriminate the way the others in this class do: it passes just as
        well against Django's stock form, because that sends nothing for an
        unknown address either. It is here because the override sits between
        "which users match" and "send the mail" -- overriding save() instead of
        send_mail(), or adding any fallback that sends when the user list is
        empty, would break this silently while the flow still looked right in a
        browser.

        What it pins is that the two responses are the same. If someone later
        adds a helpful "no account with that address" message, this fails --
        which is the realistic regression. It does not cover timing-based
        enumeration: a known address renders templates and queues a task while
        an unknown one returns immediately. That difference exists in Django
        itself and is out of scope here.
        """
        known = self.client.post(reverse('accounts-password_reset'),
                                 {'email': 'user1@example.com'}, follow=True)
        self.assertEqual(send_mail_mock.call_count, 1)

        send_mail_mock.reset_mock()
        unknown = self.client.post(reverse('accounts-password_reset'),
                                   {'email': 'nobody@example.com'},
                                   follow=True)
        self.assertEqual(send_mail_mock.call_count, 0)

        # Same status, same landing page, same rendered body: nothing in the
        # response tells the caller whether the address has an account.
        self.assertEqual(unknown.status_code, known.status_code)
        self.assertEqual(unknown.redirect_chain, known.redirect_chain)
        self.assertEqual(unknown.content, known.content)


class LogoutTest(TestCase):
    """
    Tests for the logout view.

    This view had no coverage at all until it broke. Every other test in the
    project logs out with `self.client.logout()`, which clears the session
    directly and never routes through the URL, so the view was never once
    requested -- which is why a deprecation warning that the test suite would
    otherwise have turned into an error went unseen for two Django versions,
    and logging out started returning 405 instead.

    """
    def setUp(self):
        User.objects.create_user('user1', 'user1@example.com', 'pw')
        self.client.login(username='user1', password='pw')

    def logged_in(self):
        return '_auth_user_id' in self.client.session

    def test_post_logs_the_user_out(self):
        """The supported method, and the one the navbars submit."""
        self.assertTrue(self.logged_in())

        response = self.client.post(reverse('accounts-logout'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.logged_in())

    def test_get_does_not_log_the_user_out(self):
        """Logging out over GET is refused, and leaves the session alone.

        Asserting the session survives matters as much as the status code: a
        logout reachable by GET can be triggered by any other site embedding
        the URL, which is why it stopped being allowed.

        """
        response = self.client.get(reverse('accounts-logout'))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.logged_in())

    def test_the_navbars_submit_logout_as_a_post(self):
        """The templates have to agree with the view, or the site cannot log out.

        A page is rendered rather than the templates being read, so this fails
        if either navbar goes back to a plain link. The two URLs are not
        interchangeable: the forums index renders `navbar.html` through
        `base.html`, and a profile renders `v3/base.html`, so between them they
        cover both of the site's navbars. Repointing either at the other design
        would quietly halve what this covers.

        """
        for url in [reverse('forums-index'), reverse('bio-me')]:
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                logout_url = reverse('accounts-logout')

                self.assertIn(f'action="{logout_url}" method="post"', html)
                self.assertNotIn(f'<a href="{logout_url}"', html)
                self.assertIn('csrfmiddlewaretoken', html)


class EmailChangeConfirmTestCase(TestCase):
    """Following the link from the new mailbox.

    Confirming deliberately does not require a login: the link is read in the
    new mailbox, which may well be on another device. Possession of the token
    is the proof, which is why the token is compared rather than looked up.

    """

    def setUp(self):
        self.user = User.objects.create_user('paul', 'paul@example.com', 'pw')
        self.change = PendingEmailChange.objects.request_change(
            self.user, 'new@example.com')

    def confirm_url(self, key=None, username=None):
        return reverse('accounts-email_change_confirm', kwargs={
            'username': username or self.user.username,
            'key': key or self.change.key,
        })

    def expire(self):
        PendingEmailChange.objects.filter(pk=self.change.pk).update(
            date_requested=timezone.now() - EMAIL_CHANGE_EXPIRATION
                           - datetime.timedelta(minutes=1))

    def test_a_valid_link_applies_the_change(self):
        response = self.client.get(self.confirm_url())

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')
        self.assertFalse(PendingEmailChange.objects.exists())

    def test_a_valid_link_works_while_logged_in(self):
        self.client.login(username='paul', password='pw')

        self.client.get(self.confirm_url())

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')

    def test_an_expired_link_is_refused_and_says_so(self):
        self.expire()

        response = self.client.get(self.confirm_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'expired')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'paul@example.com')

    def test_a_wrong_key_is_refused(self):
        response = self.client.get(self.confirm_url(key=make_confirmation_token()))

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'paul@example.com')
        self.assertTrue(PendingEmailChange.objects.exists())

    def test_an_unknown_user_is_refused(self):
        response = self.client.get(self.confirm_url(username='nobody'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nobody').exists())

    def test_an_address_claimed_in_the_meantime_is_refused(self):
        """Two members can request the same free address and both confirm.

        The form check cannot see this coming -- at request time neither
        account held the address -- so the last write is guarded here too.
        Without it this flow mints exactly the kind of duplicate pair it
        exists to prevent.

        """
        User.objects.create_user('eddie', 'new@example.com', 'pw')

        response = self.client.get(self.confirm_url())

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'paul@example.com')

    def test_the_key_is_a_csprng_token(self):
        self.assertGreaterEqual(len(self.change.key), 32)
        self.assertTrue(re.match(r'^[A-Za-z0-9_-]+$', self.change.key),
                        msg='key is not a URL-safe token: %r' % self.change.key)

    def test_the_route_accepts_the_tokens_the_helper_mints(self):
        # A 43-character URL-safe token contains '-' and '_' and is far longer
        # than the 20-character alphanumeric keys the registration route was
        # originally written for. Minting a batch is cheap insurance against a
        # pattern that happens to match the one token a fixture chose.
        for _ in range(50):
            key = make_confirmation_token()
            with self.subTest(key=key):
                self.confirm_url(key=key)
