"""
Unit tests for the contact application views.

"""
from unittest.mock import patch, Mock
from django.test import TestCase
from django.conf import settings
from django.urls import reverse
from django.core import mail


class BaseTestCase(TestCase):
    """Simple tests to ensure basic functionality."""

    def setUp(self):
        self.url = reverse('contact-form')

    @patch('contact.forms.requests.post')
    def test_usage(self, post_mock):
        post_response = Mock()
        post_response.json.return_value = {'success': True}
        post_mock.return_value = post_response

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
            'g-recaptcha-response': 'crazy-google-string',
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertRedirects(response, reverse('contact-thanks'))

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.recipients()), 1)
        self.assertEqual(email.extra_headers['Reply-To'], post_data['email'])
        self.assertEqual(email.from_email, 'no_reply@example.com')
        self.assertEqual(email.recipients()[0], 'admin@surfguitar101.com')
        self.assertTrue(post_data['subject'] in email.subject)
        msg = email.message().as_string()
        self.assertTrue(post_data['name'] in msg)
        self.assertTrue(post_data['email'] in msg)
        self.assertTrue(post_data['message'] in msg)

        post_mock.assert_called_once_with(settings.RECAPTCHA_URL, data={
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': 'crazy-google-string',
            'remoteip': '127.0.0.1',
        })

    def test_honeypot(self):
        post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
            'honeypot': 'some spam',
        }
        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_no_captcha_response(self):
        post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    @patch('contact.forms.requests.post')
    def test_captcha_failure(self, post_mock):
        post_response = Mock()
        post_response.json.return_value = {'success': False}
        post_mock.return_value = post_response

        post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
            'g-recaptcha-response': 'crazy-google-string',
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
