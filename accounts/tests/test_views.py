"""
View tests for the accounts application.

"""
import datetime
import re

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password

from accounts.models import PendingUser
from accounts.models import IllegalUsername
from accounts.models import IllegalEmail


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
            date_joined=datetime.datetime.now(),
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
            'question4': u'2',
            'question5': u'328',
            'question6': u'4',
            'question7': [u'2', u'4', u'5', u'7'],
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
            })

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

    def test_illegal_username(self):
        """
        Ensure we can't register with a banned username.

        """
        self.post_vals['username'] = 'illegalusername'
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

    def test_duplicate_pending_email(self):
        """
        Ensure we can't register with a duplicate email address.

        """
        self.post_vals['email'] = 'pending_user@example.com'
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

    def test_password_match(self):
        """
        Ensure the passwords match.

        """
        self.post_vals['password2'] = "doesn't match"
        response = self.client.post(reverse('accounts-register'),
            self.post_vals)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn&#39;t match")

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

    def test_question4(self):
        """
        Ensure our security question 4 works

        """
        self.post_vals['question4'] = u'1'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question4'] = u'4'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question4'] = u'8'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

    def test_question5(self):
        """
        Ensure our security question 5 works

        """
        self.post_vals['question5'] = u'1'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question5'] = u'X'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question5'] = u'2983'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

    def test_question6(self):
        """
        Ensure our security question 6 works

        """
        self.post_vals['question6'] = u'1'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question6'] = u'2'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question6'] = u'8'
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

    def test_question7(self):
        """Test security question 7"""

        self.post_vals['question7'] = []
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question7'] = [u'1']
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question7'] = [u'6', u'2', u'4', u'5', u'7']
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

        self.post_vals['question7'] = [u'4', u'3', u'7']
        response = self.client.post(reverse('accounts-register'),
             self.post_vals)
        self.assertEqual(response.status_code, 200)

    def test_success(self):
        """
        Ensure we can successfully register.

        """
        response = self.client.post(reverse('accounts-register'),
                self.post_vals)
        self.assertEqual(response.status_code, 302)

        try:
            pending = PendingUser.objects.get(username='a_new_user')
        except PendingUser.DoesNotExist:
            self.fail("PendingUser was not created")

        self.assertEqual(pending.email, 'test@example.com')
        self.assertTrue(datetime.datetime.now() - pending.date_joined <
                datetime.timedelta(minutes=1))
        self.assertTrue(check_password('my_password', pending.password))


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
        if (len(mail.outbox)):
            msg = mail.outbox[0]
            self.assertTrue(msg.subject.startswith('Password reset'))
            self.assertTrue(len(msg.to) == 1 and msg.to[0] == 'user1@example.com')
            msg_text = msg.message().as_string()
            m = re.search(r'http://example.com/accounts/password/reset/confirm/'
                r'(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9a-z]+-\w+)/',
                msg_text)
            self.assertTrue(m is not None)
            if m:
                uidb64, token = m.group('uidb64'), m.group('token')

            # visit the password reset page
            response = self.client.get(
                    reverse('accounts-password_reset_confirm',
                            kwargs={'uidb64': uidb64, 'token': token}))
            self.assertEqual(response.status_code, 200)

            # POST new password
            args = {'new_password1': 'pw2', 'new_password2': 'pw2'}
            response = self.client.post(
                    reverse('accounts-password_reset_confirm',
                            kwargs={'uidb64': uidb64, 'token': token}),
                    args, follow=True)
            self.assertRedirects(response,
                    reverse('accounts-password_reset_success'))
            self.assertEqual(response.status_code, 200)

            # Check new password
            u = User.objects.get(username='user1')
            self.assertTrue(check_password('pw2', u.password))
