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
from django.conf import settings
from django.utils import timezone

from accounts.models import PendingUser
from accounts.models import IllegalUsername
from accounts.models import IllegalEmail
from accounts.utils import make_confirmation_token


class RegistrationTest(TestCase):

    def setUp(self):
        u = User.objects.create_user('existing_user', 'existing_user@example.com', 'pw')
        u.save()

        # a 2nd user has the same email as another
        u = User.objects.create_user('existing_user2', 'existing_user@example.com', 'pw')
        u.save()

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
            'question1': '101',
            'question2': '',
            'question3': '',
        }

    def test_get_view(self):
        """
        Test a simple get of the registration view

        """
        response = self.client.get(reverse('accounts-register'))
        self.assertEqual(response.status_code, 200)

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
            'question1': '101',
            'question2': '',
            'question3': '',
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

    def test_question1(self):
        """
        Ensure our anti-spam question is answered.

        """
        self.post_vals['question1'] = 'huh'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect answer to our anti-spam question")

    def test_question2(self):
        """
        Ensure our honeypot question check works.

        """
        self.post_vals['question2'] = 'non blank'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

    def test_question3(self):
        """
        Ensure our non-hidden honeypot question check works.

        """
        self.post_vals['question3'] = 'non blank'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

    def test_success(self):
        """
        Ensure we can successfully register.

        """
        response = self.client.post(reverse('accounts-register'),
                self.post_vals)
        self.assertRedirects(response, reverse('accounts-register1'))

        # No pending user should exist yet
        try:
            pending = PendingUser.objects.get(username='a_new_user')
        except PendingUser.DoesNotExist:
            pass
        else:
            self.fail("PendingUser was created early")

        # Should have created a reg_info dict in the session
        reg_info = self.client.session.get('reg_info')
        self.assertEqual(reg_info, {
            'username': self.post_vals['username'],
            'email': self.post_vals['email'],
            'password': self.post_vals['password1'],
            'code': reg_info['code'],
            })
        code = reg_info['code']
        match = re.match(r'\w+-\d{3}', code)
        self.assertIsNotNone(match)

        # Get the next page
        response = self.client.get(reverse('accounts-register2'))
        self.assertEqual(response.status_code, 200)

        # No pending user should exist yet
        try:
            pending = PendingUser.objects.get(username='a_new_user')
        except PendingUser.DoesNotExist:
            pass
        else:
            self.fail("PendingUser was created early")

        # Try bad code
        response = self.client.post(reverse('accounts-register2'),
                                    {'code': code + code })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The registration code does not match")

        # No pending user should exist yet
        try:
            pending = PendingUser.objects.get(username='a_new_user')
        except PendingUser.DoesNotExist:
            pass
        else:
            self.fail("PendingUser was created early")

        # Try good code
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('email', level='INFO') as logged:
            response = self.client.post(reverse('accounts-register2'),
                                        {'code': code })
        self.assertIn('category=registration', logged.output[0])
        self.assertRedirects(response, reverse('accounts-register_thanks'))
        self.assertIsNone(self.client.session.get('reg_info'))

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
            pending = PendingUser.objects.get(username='a_new_user')
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

        Thirteen addresses in the production database are held by two users
        each, so this is reachable in the wild -- and was a 500 before the
        lookup stopped assuming a single match. Whoever reads the mailbox owns
        both accounts, so naming only one of them would leave them stuck on the
        other.

        """
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
