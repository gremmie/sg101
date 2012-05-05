"""
View tests for the accounts application.

"""
import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password

from antispam.rate_limit import unblock_ip
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

    def tearDown(self):
        unblock_ip('127.0.0.1')

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
        response = self.client.post(reverse('accounts-register'), {
            'username': 'pending_user',
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
        self.assertContains(response, 'A pending user with that username already exists')

    def test_illegal_username(self):
        """
        Ensure we can't register with a banned username.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'illegalusername',
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
        self.assertContains(response, 'That username is not allowed')

    def test_duplicate_existing_email(self):
        """
        Ensure we can't register with a duplicate email address.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'a_new_user',
            'email': 'existing_user@example.com',
            'password1': 'my_password',
            'password2': 'my_password',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question1': '101',
            'question2': '',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that email address already exists')

    def test_duplicate_pending_email(self):
        """
        Ensure we can't register with a duplicate email address.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'a_new_user',
            'email': 'pending_user@example.com',
            'password1': 'my_password',
            'password2': 'my_password',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question1': '101',
            'question2': '',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A pending user with that email address already exists')

    def test_illegal_email(self):
        """
        Ensure we can't register with a banned email address.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'a_new_user',
            'email': 'illegal@example.com',
            'password1': 'my_password',
            'password2': 'my_password',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question1': '101',
            'question2': '',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That email address is not allowed')

    def test_password_match(self):
        """
        Ensure the passwords match.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'a_new_user',
            'email': 'test@example.com',
            'password1': 'my_password',
            'password2': 'my_password_doesnt match',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question1': '101',
            'question2': '',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn&#39;t match")

    def test_question1(self):
        """
        Ensure our anti-spam question is answered.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'a_new_user',
            'email': 'test@example.com',
            'password1': 'my_password',
            'password2': 'my_password_doesnt match',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question1': 'huh',
            'question2': '',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect answer to our anti-spam question")

    def test_question2(self):
        """
        Ensure our honeypot question check works.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'a_new_user',
            'email': 'test@example.com',
            'password1': 'my_password',
            'password2': 'my_password_doesnt match',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question1': '101',
            'question2': 'non blank',
            })

        self.assertEqual(response.status_code, 403)

    def test_success(self):
        """
        Ensure we can successfully register.

        """
        response = self.client.post(reverse('accounts-register'), {
            'username': 'a_new_user',
            'email': 'test@example.com',
            'password1': 'my_password',
            'password2': 'my_password',
            'agree_age': 'on',
            'agree_tos': 'on',
            'agree_privacy': 'on',
            'question1': '101',
            'question2': '',
            })

        self.assertEqual(response.status_code, 302)

        try:
            pending = PendingUser.objects.get(username='a_new_user')
        except PendingUser.DoesNotExist:
            self.fail("PendingUser was not created")

        self.assertEqual(pending.email, 'test@example.com')
        self.assertTrue(datetime.datetime.now() - pending.date_joined <
                datetime.timedelta(minutes=1))
        self.assertTrue(check_password('my_password', pending.password))
