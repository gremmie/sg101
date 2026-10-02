"""
Tests for the allowlisting email backend.

The SMTP backend's own send_messages is patched out, so these see exactly what
would have gone to the mail server and nothing is ever sent.

"""
import logging
from unittest import mock

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.mail import mail_admins
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.test import SimpleTestCase
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from core.email_categories import EmailCategory
from core.functions import send_mail
from core.mail_backends import AllowlistEmailBackend


@override_settings(EMAIL_ALLOWLIST=['tester@example.com', 'Brian@Example.com'])
class AllowlistEmailBackendTestCase(SimpleTestCase):

    def setUp(self):
        patcher = mock.patch.object(SMTPBackend, 'send_messages',
                                    side_effect=lambda messages: len(messages))
        self.smtp_send = patcher.start()
        self.addCleanup(patcher.stop)

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

    def send(self, *messages):
        return AllowlistEmailBackend().send_messages(list(messages))

    def sent_messages(self):
        """The messages handed on to the SMTP backend, across every call."""
        return [message for call in self.smtp_send.call_args_list
                for message in call.args[0]]

    def test_only_listed_addresses_are_kept_in_every_field(self):
        message = EmailMessage(
                'Reply', 'Body', 'admin@example.com',
                to=['tester@example.com', 'member@example.com'],
                cc=['brian@example.com', 'other@example.com'],
                bcc=['tester@example.com', 'third@example.com'])

        sent = self.send(message)

        self.assertEqual(sent, 1)
        [delivered] = self.sent_messages()
        self.assertEqual(delivered.to, ['tester@example.com'])
        self.assertEqual(delivered.cc, ['brian@example.com'])
        self.assertEqual(delivered.bcc, ['tester@example.com'])

    def test_a_message_with_no_listed_recipient_is_not_sent(self):
        message = EmailMessage('Reply', 'Body', 'admin@example.com',
                               to=['member@example.com'],
                               cc=['other@example.com'])

        sent = self.send(message)

        self.assertEqual(sent, 0)
        self.assertEqual(self.sent_messages(), [])

    def test_only_the_messages_with_a_listed_recipient_are_sent(self):
        kept = EmailMessage('One', 'Body', 'admin@example.com',
                            to=['tester@example.com'])
        dropped = EmailMessage('Two', 'Body', 'admin@example.com',
                               to=['member@example.com'])

        sent = self.send(dropped, kept)

        self.assertEqual(sent, 1)
        self.assertEqual(self.sent_messages(), [kept])

    def test_matching_ignores_case(self):
        message = EmailMessage('Reply', 'Body', 'admin@example.com',
                               to=['TESTER@Example.COM', 'brian@example.com'])

        self.send(message)

        [delivered] = self.sent_messages()
        self.assertEqual(delivered.to,
                         ['TESTER@Example.COM', 'brian@example.com'])

    def test_a_named_address_matches_on_its_address(self):
        # mail_admins and a member's display name both produce this form.
        message = EmailMessage('Reply', 'Body', 'admin@example.com',
                               to=['Jeff Tester <tester@example.com>',
                                   'Tester Lookalike <member@example.com>'])

        self.send(message)

        [delivered] = self.sent_messages()
        self.assertEqual(delivered.to, ['Jeff Tester <tester@example.com>'])

    @override_settings(EMAIL_ALLOWLIST=[])
    def test_an_empty_allowlist_sends_nothing(self):
        message = EmailMessage('Reply', 'Body', 'admin@example.com',
                               to=['tester@example.com'])

        sent = self.send(message)

        self.assertEqual(sent, 0)
        self.assertEqual(self.sent_messages(), [])

    @override_settings(EMAIL_ALLOWLIST=['', '  '])
    def test_an_allowlist_of_blanks_sends_nothing(self):
        # What a variable set to an empty string can parse to.
        message = EmailMessage('Reply', 'Body', 'admin@example.com',
                               to=['tester@example.com', ''])

        sent = self.send(message)

        self.assertEqual(sent, 0)
        self.assertEqual(self.sent_messages(), [])

    def test_a_missing_allowlist_sends_nothing(self):
        message = EmailMessage('Reply', 'Body', 'admin@example.com',
                               to=['tester@example.com'])

        with self.settings():
            from django.conf import settings
            del settings.EMAIL_ALLOWLIST
            sent = self.send(message)

        self.assertEqual(sent, 0)
        self.assertEqual(self.sent_messages(), [])

    def test_each_dropped_address_is_logged(self):
        message = EmailMessage('A member wrote this', 'Body',
                               'admin@example.com',
                               to=['tester@example.com', 'member@example.com'],
                               bcc=['third@example.com'])

        with self.assertLogs('email', level='INFO') as logged:
            self.send(message)

        self.assertEqual(len(logged.records), 2)
        output = '\n'.join(logged.output)
        self.assertIn('field=to to=member@example.com', output)
        self.assertIn('field=bcc to=third@example.com', output)
        self.assertNotIn('tester@example.com', output)
        # The subject can be a member's own words, and log_send keeps those
        # out of the log too.
        self.assertNotIn('A member wrote this', output)

    def test_a_message_left_with_no_recipients_is_logged(self):
        message = EmailMessage('Reply', 'Body', 'admin@example.com',
                               to=['member@example.com'])

        with self.assertLogs('email', level='INFO') as logged:
            self.send(message)

        self.assertIn('outcome=not sent, no allowlisted recipient',
                      logged.output[-1])


@override_settings(
        EMAIL_BACKEND='core.mail_backends.AllowlistEmailBackend',
        EMAIL_ALLOWLIST=['tester@example.com', 'brian@example.com'],
        ADMINS=[('Brian', 'brian@example.com'), ('Other', 'other@example.com')])
class MailPathTestCase(TestCase):
    """
    The site's mail paths, each sending through the backend once it is chosen.

    Not every path goes through core.functions.send_mail, which is why the
    filter is a backend; these check that the ones that do not still reach it.

    """
    def setUp(self):
        patcher = mock.patch.object(SMTPBackend, 'send_messages',
                                    side_effect=lambda messages: len(messages))
        self.smtp_send = patcher.start()
        self.addCleanup(patcher.stop)

    def delivered_to(self):
        return [message.recipients() for call in self.smtp_send.call_args_list
                for message in call.args[0]]

    def test_the_sites_send_mail(self):
        send_mail('Reply', 'Body', 'admin@example.com',
                  ['tester@example.com', 'member@example.com'],
                  category=EmailCategory.PM_NOTIFICATION)

        self.assertEqual(self.delivered_to(), [['tester@example.com']])

    def test_djangos_mail_admins(self):
        # What AdminEmailHandler calls when a request raises.
        mail_admins('Internal Server Error', 'Traceback')

        self.assertEqual(self.delivered_to(), [['brian@example.com']])

    def test_a_password_reset(self):
        User.objects.create_user('kahuna', 'tester@example.com', 'pw')
        User.objects.create_user('wahini', 'member@example.com', 'pw')

        for address in ('tester@example.com', 'member@example.com'):
            self.client.post(reverse('accounts-password_reset'),
                             {'email': address})

        self.assertEqual(self.delivered_to(), [['tester@example.com']])
