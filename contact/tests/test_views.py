"""
Unit tests for the contact application views.

"""
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail


class BaseTestCase(TestCase):
    """Simple tests to ensure basic functionality."""

    def test_usage(self):
        url = reverse('contact-form')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
        }
        response = self.client.post(url, data=post_data, follow=True)
        self.assertRedirects(response, reverse('contact-thanks'))

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.recipients()), 1)
        self.assertEqual(email.from_email, post_data['email'])
        self.assertEqual(email.recipients()[0], 'admin@surfguitar101.com')
        self.assertTrue(post_data['subject'] in email.subject)
        msg = email.message().as_string()
        self.assertTrue(post_data['name'] in msg)
        self.assertTrue(post_data['email'] in msg)
        self.assertTrue(post_data['message'] in msg)

    def test_honeypot(self):
        url = reverse('contact-form')
        post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
            'honeypot': 'some spam',
        }
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
