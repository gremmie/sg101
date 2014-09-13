"""
Unit tests for the messages application views.

"""
import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core import mail

import messages
from messages.models import Message, Options, Flag


class NotLoggedInTestCase(TestCase):
    """Ensure we are redirected to the login page before we can do anything with
    this application.

    """
    LOGIN_URL = reverse('accounts-login')

    def _test_get(self, url_name, **kwargs):
        url = reverse(url_name, **kwargs)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + '?next=' + url)

    def _test_post(self, url_name, **kwargs):
        url = reverse(url_name, **kwargs)
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + '?next=' + url)

    def test_inbox(self):
        self._test_get('messages-inbox')

    def test_compose(self):
        url_name = 'messages-compose'
        self._test_get(url_name)
        self._test_post(url_name)

    def test_outbox(self):
        self._test_get('messages-outbox')

    def test_trash(self):
        self._test_get('messages-trash')

    def test_options(self):
        url_name = 'messages-options'
        self._test_get(url_name)
        self._test_post(url_name)

    def test_delete(self):
        self._test_get('messages-bulk')

    def test_undelete(self):
        self._test_get('messages-undelete')

    def test_view(self):
        url_name = 'messages-view'
        self._test_get(url_name, args=[123])
        self._test_post(url_name, args=[123])

    def test_report(self):
        url_name = 'messages-report'
        self._test_get(url_name, args=[123])
        self._test_post(url_name, args=[123])


class BasicTestCase(TestCase):
    """Testing a logged in user visiting all the views with no messages."""
    fixtures = ['messages_test_users.json']
    MSG_BOX_LIMIT = 3

    def setUp(self):
        self.users = {}
        self.users['pj'] = User.objects.get(username='pj')
        self.users['pj'].set_password('12345')
        self.users['pj'].save()
        self.assertTrue(self.client.login(username='pj', password='12345'))

        self.users['eddie'] = User.objects.get(username='eddie')
        self.users['eddie'].set_password('12345')
        self.users['eddie'].save()

        self.users['richard'] = User.objects.get(username='richard')
        self.users['richard'].set_password('12345')
        self.users['richard'].save()

        # To reduce test duration, reduce MSG_BOX_LIMIT
        self.saved_msg_box_limit = messages.MSG_BOX_LIMIT
        messages.MSG_BOX_LIMIT = self.MSG_BOX_LIMIT

    def tearDown(self):
        messages.MSG_BOX_LIMIT = self.saved_msg_box_limit

    def test_simple_gets(self):
        view_names = [
            'messages-inbox',
            'messages-compose',
            'messages-outbox',
            'messages-trash',
            'messages-options',
        ]
        for view_name in view_names:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)

    def test_wrong_method(self):
        view_names = [
            'messages-bulk',
            'messages-undelete',
        ]
        for view_name in view_names:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 405)

    def test_nonexistent_pms(self):
        view_names = [
            'messages-view',
            'messages-report',
        ]
        for view_name in view_names:
            response = self.client.get(reverse(view_name, args=[42]))
            self.assertEqual(response.status_code, 404)

            response = self.client.post(reverse(view_name, args=[42]))
            self.assertEqual(response.status_code, 404)

    def test_options(self):
        view_name = 'messages-options'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'opts-attach_signature': 'on',
            'opts-notify_email': 'on',
        }
        response = self.client.post(url, data=post_data, follow=True)
        self.assertRedirects(response, url)

        opts = Options.objects.for_user(self.users['pj'])
        self.assertTrue(opts.attach_signature)
        self.assertTrue(opts.notify_email)

        post_data = {}
        response = self.client.post(url, data=post_data, follow=True)
        self.assertRedirects(response, url)

        opts = Options.objects.for_user(self.users['pj'])
        self.assertFalse(opts.attach_signature)
        self.assertFalse(opts.notify_email)

    def test_send_bogus_user(self):
        post_data = {
            'receiver': 'unknown_user',
            'subject': 'hi',
            'message': 'test',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data)
        self.assertContains(response, 'username does not exist', status_code=200)

        qs = Message.objects.filter(sender=self.users['pj'])
        self.assertEqual(qs.count(), 0)

    def test_send_to_self(self):
        post_data = {
            'receiver': 'pj',
            'subject': 'hi',
            'message': 'test',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data)
        self.assertContains(response, "You can&#39;t send a message to yourself", status_code=200)

        qs = Message.objects.filter(sender=self.users['pj'])
        self.assertEqual(qs.count(), 0)

    def test_message_cycle(self):
        # pj sends message to eddie
        now = datetime.datetime.now()
        post_data = {
            'receiver': 'eddie',
            'subject': 'Mr. Moto Demo',
            'message': 'Gig at Newport High School',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data)
        self.assertContains(response, "Message sent", status_code=200)

        # see if message got created in database
        msg = Message.objects.get(sender=self.users['pj'])

        self.assertEqual(msg.sender, self.users['pj'])
        self.assertEqual(msg.receiver, self.users['eddie'])
        self.assertTrue(now - msg.send_date < datetime.timedelta(seconds=5))
        self.assertIsNone(msg.read_date)
        self.assertIsNone(msg.reply_date)
        self.assertEqual(msg.subject, post_data['subject'])
        self.assertEqual(msg.message, post_data['message'])
        self.assertIsNone(msg.sender_delete_date)
        self.assertIsNone(msg.receiver_delete_date)

        # see if shows up in outbox view
        view_name = 'messages-outbox'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertContains(response, post_data['subject'], status_code=200)

        # see if we can view it
        view_name = 'messages-view'
        url = reverse(view_name, args=[msg.pk])
        response = self.client.get(url)
        self.assertContains(response, post_data['subject'], status_code=200)
        self.assertContains(response, post_data['message'], status_code=200)

        # eddie logs in and checks various views
        self.assertTrue(self.client.login(username='eddie', password='12345'))
        view_name = 'messages-inbox'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertContains(response, post_data['subject'], status_code=200)
        view_name = 'messages-outbox'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertNotContains(response, post_data['subject'], status_code=200)
        view_name = 'messages-trash'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertNotContains(response, post_data['subject'], status_code=200)

        # eddie reads it
        view_name = 'messages-view'
        url = reverse(view_name, args=[msg.pk])
        response = self.client.get(url)
        self.assertContains(response, post_data['subject'], status_code=200)
        self.assertContains(response, post_data['message'], status_code=200)

        # see if message got updated in database
        msg = Message.objects.get(receiver=self.users['eddie'])

        self.assertEqual(msg.sender, self.users['pj'])
        self.assertEqual(msg.receiver, self.users['eddie'])
        self.assertTrue(now - msg.send_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg.read_date < datetime.timedelta(seconds=5))
        self.assertIsNone(msg.reply_date)
        self.assertEqual(msg.subject, post_data['subject'])
        self.assertEqual(msg.message, post_data['message'])
        self.assertIsNone(msg.sender_delete_date)
        self.assertIsNone(msg.receiver_delete_date)

        # eddie replies
        post_data2 = {
            'receiver': 'pj',
            'subject': 'Re: Mr. Moto Demo',
            'message': 'South Bay Sound',
            'parent_id': msg.pk,
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data2)
        self.assertContains(response, "Message sent", status_code=200)

        self.assertEqual(Message.objects.all().count(), 2)

        msg1 = Message.objects.get(receiver=self.users['eddie'])

        self.assertEqual(msg1.sender, self.users['pj'])
        self.assertEqual(msg1.receiver, self.users['eddie'])
        self.assertTrue(now - msg1.send_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg1.read_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg1.reply_date < datetime.timedelta(seconds=5))
        self.assertEqual(msg1.subject, post_data['subject'])
        self.assertEqual(msg1.message, post_data['message'])
        self.assertIsNone(msg1.sender_delete_date)
        self.assertIsNone(msg1.receiver_delete_date)

        msg2 = Message.objects.get(receiver=self.users['pj'])

        self.assertEqual(msg2.sender, self.users['eddie'])
        self.assertEqual(msg2.receiver, self.users['pj'])
        self.assertTrue(now - msg2.send_date < datetime.timedelta(seconds=5))
        self.assertIsNone(msg2.read_date)
        self.assertIsNone(msg2.reply_date)
        self.assertEqual(msg2.subject, post_data2['subject'])
        self.assertEqual(msg2.message, post_data2['message'])
        self.assertIsNone(msg2.sender_delete_date)
        self.assertIsNone(msg2.receiver_delete_date)

        # pj logs in and checks various views
        self.assertTrue(self.client.login(username='pj', password='12345'))
        view_name = 'messages-inbox'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertContains(response, post_data2['subject'], status_code=200)
        view_name = 'messages-outbox'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertContains(response, post_data['subject'], status_code=200)
        view_name = 'messages-trash'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertNotContains(response, post_data['subject'], status_code=200)
        self.assertNotContains(response, post_data2['subject'], status_code=200)

        # pj reads reply
        view_name = 'messages-view'
        url = reverse(view_name, args=[msg2.pk])
        response = self.client.get(url)
        self.assertContains(response, post_data2['subject'], status_code=200)
        self.assertContains(response, post_data2['message'], status_code=200)

        msg = Message.objects.get(receiver=self.users['eddie'])

        self.assertEqual(msg.sender, self.users['pj'])
        self.assertEqual(msg.receiver, self.users['eddie'])
        self.assertTrue(now - msg.send_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg.read_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg.reply_date < datetime.timedelta(seconds=5))
        self.assertEqual(msg.subject, post_data['subject'])
        self.assertEqual(msg.message, post_data['message'])
        self.assertIsNone(msg.sender_delete_date)
        self.assertIsNone(msg.receiver_delete_date)

        msg2 = Message.objects.get(receiver=self.users['pj'])

        self.assertEqual(msg2.sender, self.users['eddie'])
        self.assertEqual(msg2.receiver, self.users['pj'])
        self.assertTrue(now - msg2.send_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg2.read_date < datetime.timedelta(seconds=5))
        self.assertIsNone(msg2.reply_date)
        self.assertEqual(msg2.subject, post_data2['subject'])
        self.assertEqual(msg2.message, post_data2['message'])
        self.assertIsNone(msg2.sender_delete_date)
        self.assertIsNone(msg2.receiver_delete_date)

        # pj deletes message 2
        self.assertEqual(Message.objects.all().count(), 2)

        delete_post_data = {
            'pm_ids': [msg2.pk],
            'action': 'Delete',
        }
        view_name = 'messages-bulk'
        url = reverse(view_name)
        response = self.client.post(url, data=delete_post_data, follow=True)
        self.assertContains(response, "1 message deleted", status_code=200)

        self.assertEqual(Message.objects.all().count(), 2)

        msg2 = Message.objects.get(receiver=self.users['pj'])

        self.assertEqual(msg2.sender, self.users['eddie'])
        self.assertEqual(msg2.receiver, self.users['pj'])
        self.assertTrue(now - msg2.send_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg2.read_date < datetime.timedelta(seconds=5))
        self.assertIsNone(msg2.reply_date)
        self.assertEqual(msg2.subject, post_data2['subject'])
        self.assertEqual(msg2.message, post_data2['message'])
        self.assertIsNone(msg2.sender_delete_date)
        self.assertTrue(now - msg2.receiver_delete_date < datetime.timedelta(seconds=5))

        # should be in pj's trash now
        view_name = 'messages-trash'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertContains(response, post_data2['subject'], status_code=200)

        # eddie logs in and deletes his copy of message 2
        self.assertTrue(self.client.login(username='eddie', password='12345'))
        delete_post_data = {
            'pm_ids': [msg2.pk],
            'action': 'Delete',
        }
        view_name = 'messages-bulk'
        url = reverse(view_name)
        response = self.client.post(url, data=delete_post_data, follow=True)
        self.assertContains(response, "1 message deleted", status_code=200)

        # should be really deleted now
        self.assertEqual(Message.objects.all().count(), 1)
        view_name = 'messages-trash'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertNotContains(response, post_data2['subject'], status_code=200)

        # eddie deletes then undeletes message 1
        delete_post_data = {
            'pm_ids': [msg1.pk],
            'action': 'Delete',
        }
        view_name = 'messages-bulk'
        url = reverse(view_name)
        response = self.client.post(url, data=delete_post_data, follow=True)
        self.assertContains(response, "1 message deleted", status_code=200)

        # should not be really deleted now
        self.assertEqual(Message.objects.all().count(), 1)
        view_name = 'messages-trash'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertContains(response, post_data['subject'], status_code=200)

        msg1 = Message.objects.get(receiver=self.users['eddie'])

        self.assertEqual(msg1.sender, self.users['pj'])
        self.assertEqual(msg1.receiver, self.users['eddie'])
        self.assertTrue(now - msg1.send_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg1.read_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg1.reply_date < datetime.timedelta(seconds=5))
        self.assertEqual(msg1.subject, post_data['subject'])
        self.assertEqual(msg1.message, post_data['message'])
        self.assertIsNone(msg1.sender_delete_date)
        self.assertTrue(now - msg1.receiver_delete_date < datetime.timedelta(seconds=5))

        delete_post_data = {
            'pm_ids': [msg1.pk],
        }
        view_name = 'messages-undelete'
        url = reverse(view_name)
        response = self.client.post(url, data=delete_post_data, follow=True)
        self.assertContains(response, "1 message undeleted", status_code=200)

        # should not be really deleted now
        self.assertEqual(Message.objects.all().count(), 1)
        view_name = 'messages-trash'
        url = reverse(view_name)
        response = self.client.get(url)
        self.assertNotContains(response, post_data['subject'], status_code=200)

        msg1 = Message.objects.get(receiver=self.users['eddie'])

        self.assertEqual(msg1.sender, self.users['pj'])
        self.assertEqual(msg1.receiver, self.users['eddie'])
        self.assertTrue(now - msg1.send_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg1.read_date < datetime.timedelta(seconds=5))
        self.assertTrue(now - msg1.reply_date < datetime.timedelta(seconds=5))
        self.assertEqual(msg1.subject, post_data['subject'])
        self.assertEqual(msg1.message, post_data['message'])
        self.assertIsNone(msg1.sender_delete_date)
        self.assertIsNone(msg1.receiver_delete_date)

    def test_read_permission(self):

        now = datetime.datetime.now()
        # pj sends a PM to richard
        post_data = {
            'receiver': 'richard',
            'subject': 'Mr. Moto Demo',
            'message': 'Gig at Newport High School',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data)
        self.assertContains(response, "Message sent", status_code=200)

        msg = Message.objects.get(sender=self.users['pj'])

        # eddie should not be able to read it
        self.assertTrue(self.client.login(username='eddie', password='12345'))
        view_name = 'messages-view'
        url = reverse(view_name, args=[msg.pk])
        response = self.client.get(url)
        self.assertNotContains(response, post_data['subject'], status_code=302)
        self.assertNotContains(response, post_data['message'], status_code=302)

        response = self.client.get(url, follow=True)
        self.assertNotContains(response, post_data['subject'], status_code=200)
        self.assertNotContains(response, post_data['message'], status_code=200)

        msg = Message.objects.get(sender=self.users['pj'])

        self.assertEqual(msg.sender, self.users['pj'])
        self.assertEqual(msg.receiver, self.users['richard'])
        self.assertTrue(now - msg.send_date < datetime.timedelta(seconds=5))
        self.assertIsNone(msg.read_date)
        self.assertIsNone(msg.reply_date)
        self.assertEqual(msg.subject, post_data['subject'])
        self.assertEqual(msg.message, post_data['message'])
        self.assertIsNone(msg.sender_delete_date)
        self.assertIsNone(msg.receiver_delete_date)

    def test_report_message(self):
        post_data = {
            'receiver': 'eddie',
            'subject': 'Mr. Moto Demo',
            'message': 'Gig at Newport High School',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data)
        self.assertContains(response, "Message sent", status_code=200)

        msg = Message.objects.get(sender=self.users['pj'])

        # Ensure non-recipients can't report a message
        view_name = 'messages-report'
        url = reverse(view_name, args=[msg.pk])
        response = self.client.post(url, data={}, follow=True)
        self.assertContains(response, "You can&#39;t report this message", status_code=200)
        self.assertEqual(Flag.objects.count(), 0)

        self.assertTrue(self.client.login(username='richard', password='12345'))
        response = self.client.post(url, data={}, follow=True)
        self.assertContains(response, "You can&#39;t report this message", status_code=200)
        self.assertEqual(Flag.objects.count(), 0)

        # Test bogus report
        self.assertTrue(self.client.login(username='eddie', password='12345'))
        bad_url = reverse(view_name, args=[msg.pk + 1])
        response = self.client.post(bad_url, data={})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Flag.objects.count(), 0)

        # Test get of report view
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Test posting to report view
        post_data = {
            'comments': 'This is abuse!',
        }
        now = datetime.datetime.now()
        response = self.client.post(url, data=post_data, follow=True)
        self.assertContains(response, "Message reported", status_code=200)

        self.assertEqual(Flag.objects.count(), 1)
        msg = Message.objects.get(receiver=self.users['eddie'])

        try:
            flag = msg.flag
        except Flag.DoesNotExist:
            self.fail("msg.flag does not exist!")

        self.assertEqual(flag.message, msg)
        self.assertTrue(now - flag.flag_date < datetime.timedelta(seconds=2))
        self.assertEqual(flag.comments, post_data['comments'])

        # Admin should have been sent an email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.recipients()), 1)
        self.assertEqual(email.recipients()[0], 'admin@surfguitar101.com')
        self.assertTrue(email.subject.endswith('A user has flagged a private message'))

    def test_inbox_full(self):

        post_data = {
            'receiver': 'eddie',
            'subject': 'Mr. Moto Demo',
            'message': 'Gig at Newport High School',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        for n in range(self.MSG_BOX_LIMIT):
            response = self.client.post(url, data=post_data)
        self.assertEqual(Message.objects.all().count(), self.MSG_BOX_LIMIT)

        # pj deletes a message so we can make sure we are testing inbox full
        msg = Message.objects.filter(receiver=self.users['eddie']).last()
        msg.sender_delete_date = datetime.datetime.now()
        msg.save()
        self.assertEqual(Message.objects.all().count(), self.MSG_BOX_LIMIT)
        self.assertEqual(Message.objects.outbox(self.users['pj']).count(),
                self.MSG_BOX_LIMIT - 1)
        self.assertEqual(Message.objects.inbox(self.users['eddie']).count(),
                self.MSG_BOX_LIMIT)

        # pj should not be able to send another
        response = self.client.post(url, data=post_data)
        self.assertNotContains(response, "Message sent", status_code=200)
        self.assertContains(response, "inbox is full", status_code=200)
        self.assertEqual(Message.objects.all().count(), self.MSG_BOX_LIMIT)

    def test_outbox_full(self):

        post_data = {
            'receiver': 'eddie',
            'subject': 'Mr. Moto Demo',
            'message': 'Gig at Newport High School',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        for n in range(self.MSG_BOX_LIMIT):
            response = self.client.post(url, data=post_data)
            self.assertContains(response, "Message sent", status_code=200)
        self.assertEqual(Message.objects.all().count(), self.MSG_BOX_LIMIT)

        # eddie deletes a message so we can make sure we are testing outbox full
        msg = Message.objects.filter(receiver=self.users['eddie']).last()
        msg.read_date = datetime.datetime.now()
        msg.receiver_delete_date = msg.read_date
        msg.save()
        self.assertEqual(Message.objects.all().count(), self.MSG_BOX_LIMIT)
        self.assertEqual(Message.objects.outbox(self.users['pj']).count(),
                self.MSG_BOX_LIMIT)
        self.assertEqual(Message.objects.inbox(self.users['eddie']).count(),
                self.MSG_BOX_LIMIT - 1)

        # pj should not be able to send another
        response = self.client.post(url, data=post_data)
        self.assertNotContains(response, "Message sent", status_code=200)
        self.assertContains(response, "Your outbox is full", status_code=200)
        self.assertEqual(Message.objects.all().count(), self.MSG_BOX_LIMIT)

    def test_email_export(self):

        post_data = {
            'receiver': 'eddie',
            'subject': 'Mr. Moto Demo',
            'message': 'Gig at Newport High School',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data)
        self.assertContains(response, "Message sent", status_code=200)

        msg = Message.objects.get(receiver=self.users['eddie'])
        post_data = {
            'pm_ids': [msg.id],
            'action': 'Email',
        }
        view_name = 'messages-bulk'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data, follow=True)
        self.assertContains(response, "1 message sent to email", status_code=200)

        # Ensure email sent
        self.assertEqual(len(mail.outbox), 1)

        if len(mail.outbox) == 1:
            email = mail.outbox[0]
            self.assertEqual(len(email.recipients()), 1)
            self.assertEqual(email.recipients()[0], 'pj@example.com')
            self.assertTrue(email.subject.startswith('Private messages from'))


class EmailTestCase(TestCase):
    """Testing to ensure email is sent when PM is sent if options allow."""
    fixtures = ['messages_test_users.json']

    def setUp(self):
        self.users = {}
        self.users['pj'] = User.objects.get(username='pj')
        self.users['pj'].set_password('12345')
        self.users['pj'].save()
        self.assertTrue(self.client.login(username='pj', password='12345'))

        self.users['eddie'] = User.objects.get(username='eddie')
        self.users['eddie'].set_password('12345')
        self.users['eddie'].save()

    def _test_email(self, email_expected):
        # pj sends message to eddie
        post_data = {
            'receiver': 'eddie',
            'subject': 'Mr. Moto Demo',
            'message': 'Gig at Newport High School',
        }
        view_name = 'messages-compose'
        url = reverse(view_name)
        response = self.client.post(url, data=post_data)
        self.assertContains(response, "Message sent", status_code=200)

        # Ensure notification email sent
        count = 1 if email_expected else 0
        self.assertEqual(len(mail.outbox), count)

        if count == 1:
            email = mail.outbox[0]
            self.assertEqual(len(email.recipients()), 1)
            self.assertEqual(email.recipients()[0], 'eddie@example.com')
            self.assertTrue(email.subject.startswith('New private message'))

    def test_email_sent(self):
        # eddie elects to receive email notifications
        # Note: testing the options view is done above.
        opts = Options.objects.for_user(self.users['eddie'])
        opts.notify_email = True
        opts.save()
        self._test_email(True)

    def test_no_email(self):
        # eddie does not to elect to receive email notifications
        opts = Options.objects.for_user(self.users['eddie'])
        opts.notify_email = False
        opts.save()
        self._test_email(False)
