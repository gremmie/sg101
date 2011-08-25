"""
Tests for the rate limiting function in the antispam application.

"""
import redis
from django.test import TestCase
from django.core.urlresolvers import reverse

from antispam.rate_limit import _make_key


class RateLimitTestCase(TestCase):
    KEY = _make_key('127.0.0.1')

    def setUp(self):
        self.conn = redis.Redis(host='localhost', port=6379, db=0)
        self.conn.delete(self.KEY)

    def tearDown(self):
        self.conn.delete(self.KEY)

    def testRegistrationLockout(self):

        for i in range(1, 11):
            response = self.client.post(
                    reverse('accounts-register'),
                    {},
                    follow=True)

            if i < 10:
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'accounts/register.html')
            elif i >= 10:
                self.assertEqual(response.status_code, 403)
                self.assertTemplateUsed(response, 'antispam/blocked.html')

    def testLoginLockout(self):

        for i in range(1, 11):
            response = self.client.post(
                    reverse('accounts-login'),
                    {},
                    follow=True)

            if i < 10:
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'accounts/login.html')
            elif i >= 10:
                self.assertEqual(response.status_code, 403)
                self.assertTemplateUsed(response, 'antispam/blocked.html')

    def testHoneypotLockout(self):

        response = self.client.post(
                reverse('accounts-register'), {
                    'username': u'test_user',
                    'email': u'test_user@example.com',
                    'password1': u'password',
                    'password2': u'password',
                    'agree_age': u'on',
                    'agree_tos': u'on',
                    'agree_privacy': u'on',
                    'question1': u'101',
                    'question2': u'DsjkdE$',
                },
                follow=True)

        val = self.conn.get(self.KEY)
        self.assertEqual(val, '1000001')

        response = self.client.post(
                reverse('accounts-login'),
                {},
                follow=True)

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'antispam/blocked.html')
