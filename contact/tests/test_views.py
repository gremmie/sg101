"""
Unit tests for the contact application views.

"""
import logging

from unittest.mock import patch
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.core import mail

from antispam.turnstile import TurnstileOutcome, TurnstileResult


class BaseTestCase(TestCase):
    """Simple tests to ensure basic functionality."""

    def setUp(self):
        self.url = reverse('contact-form')
        self.post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
            'cf-turnstile-response': 'a-token',
        }

    def test_usage(self, ):
        with patch('contact.forms.turnstile.verify') as verify:
            verify.return_value = TurnstileResult(TurnstileOutcome.PASSED)

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

            old_disable = logging.getLogger().manager.disable
            logging.disable(logging.NOTSET)
            self.addCleanup(logging.disable, old_disable)

            with self.assertLogs('email', level='INFO') as logged:
                response = self.client.post(self.url, data=self.post_data,
                                            follow=True)

        # A member wrote this subject, so the log records the category in its
        # place.
        self.assertIn('category=contact_form', logged.output[0])
        self.assertNotIn('Test message', logged.output[0])
        self.assertRedirects(response, reverse('contact-thanks'))

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.recipients()), 1)
        self.assertEqual(email.extra_headers['Reply-To'],
                         self.post_data['email'])
        self.assertEqual(email.from_email, 'no_reply@example.com')
        self.assertEqual(email.recipients()[0], 'admin@surfguitar101.com')
        self.assertTrue(self.post_data['subject'] in email.subject)
        msg = email.message().as_string()
        self.assertTrue(self.post_data['name'] in msg)
        self.assertTrue(self.post_data['email'] in msg)
        self.assertTrue(self.post_data['message'] in msg)

        verify.assert_called_once_with('a-token', '127.0.0.1',
                                       source='contact form')

    def test_widget_is_rendered(self):
        """The view's context key and the template's must agree, and only a
        rendered page can say they do."""
        response = self.client.get(self.url)

        self.assertContains(response, 'cf-turnstile')
        self.assertContains(response, settings.TURNSTILE_SITE_KEY)
        self.assertContains(response,
                            'challenges.cloudflare.com/turnstile/v0/api.js')

    def test_honeypot(self):
        self.post_data['honeypot'] = 'some spam'
        response = self.client.post(self.url, data=self.post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_no_captcha_response(self):
        """A missing token is refused, and the helper is what decides.

        The form does not guard: it always calls verify(), which recognises an
        absent token and returns without reaching Cloudflare. That nothing goes
        on the wire is proven in antispam's tests, once for every caller,
        rather than here for this one.
        """
        del self.post_data['cf-turnstile-response']

        with patch('contact.forms.turnstile.verify') as verify:
            verify.return_value = TurnstileResult(TurnstileOutcome.NO_TOKEN)
            response = self.client.post(self.url, data=self.post_data,
                                        follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn('Please verify',
                      response.context['form'].non_field_errors()[0])
        # Handed over rather than short-circuited here. Asserting the call
        # first keeps a regression reading as a failure, not an AttributeError.
        verify.assert_called_once()
        self.assertFalse(verify.call_args.args[0])

    def test_captcha_failure(self):
        """A rejected challenge blocks the send and says so."""
        with patch('contact.forms.turnstile.verify') as verify:
            verify.return_value = TurnstileResult(
                TurnstileOutcome.REJECTED, ('invalid-input-response',))
            response = self.client.post(self.url, data=self.post_data,
                                        follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("couldn't verify",
                      response.context['form'].non_field_errors()[0])

    def test_captcha_unavailable_fails_open(self):
        """An outage must not take the form down with it.

        The form is not naked during the window: the honeypot still applies,
        and the helper logs the skipped check at WARNING.
        """
        with patch('contact.forms.turnstile.verify') as verify:
            verify.return_value = TurnstileResult(TurnstileOutcome.UNAVAILABLE)
            response = self.client.post(self.url, data=self.post_data,
                                        follow=True)

        self.assertRedirects(response, reverse('contact-thanks'))
        self.assertEqual(len(mail.outbox), 1)


class SubjectNewlineTests(TestCase):
    """A newline in the subject is a header injection.

    Django's forbid_multi_line_headers already refuses one, but it refuses it
    at the mail layer -- which send_mail() reaches through Celery, so the
    rejection arrives as a task crash and an admin error report carrying the
    whole submission, and the person who typed it is told nothing. These pin
    the refusal to the form, where it can be answered.
    """

    def setUp(self):
        self.url = reverse('contact-form')
        self.post_data = {
            'name': 'John Doe',
            'email': 'jdoe@example.com',
            'subject': 'Test message',
            'message': 'Testing contact form.',
            'cf-turnstile-response': 'a-token',
        }

    def post(self, subject):
        self.post_data['subject'] = subject
        with patch('contact.forms.turnstile.verify') as verify:
            verify.return_value = TurnstileResult(TurnstileOutcome.PASSED)
            return self.client.post(self.url, data=self.post_data, follow=True)

    def assertRefused(self, subject):
        response = self.post(subject)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn('line breaks',
                      response.context['form'].errors['subject'][0])

    def test_embedded_crlf_is_refused(self):
        """The shape that arrived in production, minus the trailing newline.

        Also the one case that checks the message reaches the page. The form
        object having an error and the reader being told are different claims,
        and only the rendered body settles the second.
        """
        response = self.post('Test message\r\nX-Injected: 1')

        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, 'Subject cannot contain line breaks')

    def test_embedded_lf_is_refused(self):
        self.assertRefused('Test\nmessage')

    def test_embedded_cr_is_refused(self):
        """A lone CR terminates no header, but it has no business here."""
        self.assertRefused('Test\rmessage')

    def test_trailing_newline_is_stripped_not_refused(self):
        """The payload that actually arrived, which is already safe.

        CharField strips it before clean_subject() ever sees it, so the subject
        reaches the header clean and the mail goes out. That safety is a Django
        default rather than anything this form does, which is why it is pinned
        here: an upgrade that changed it would otherwise go unnoticed.
        """
        response = self.post('Test message\r\n')

        self.assertRedirects(response, reverse('contact-thanks'))
        self.assertEqual(len(mail.outbox), 1)
        subject = mail.outbox[0].subject
        self.assertTrue(subject.endswith('Test message'))
        self.assertNotIn('\n', subject)
        self.assertNotIn('\r', subject)
