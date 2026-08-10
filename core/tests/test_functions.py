import unittest

from django.http.request import HttpRequest
from django.utils import timezone
from mock import call, patch, mock_open, Mock

from core.functions import (TemporaryFile, remove_file, send_mail, email_admins,
    email_managers, get_full_name, copyright_str, get_ip, get_page, is_ajax,
    quote_message)


class TemporaryFileTestCase(unittest.TestCase):
    @patch('core.functions.tempfile')
    @patch('core.functions.os')
    def test_basic_operation(self, os_mock, tempfile_mock):
        tempfile_mock.mkstemp.return_value = (42, 'temp.txt')

        with TemporaryFile(suffix='.txt') as temp:
            temp.file.write('contents')
            self.assertEqual(temp.fd, 42)
            self.assertEqual(temp.filename, 'temp.txt')

        self.assertEqual(tempfile_mock.mkstemp.mock_calls, [
            call(suffix='.txt'),
        ])
        self.assertEqual(os_mock.fdopen.mock_calls, [
            call(42, 'w+b'), call().write('contents'), call().close(),
        ])
        self.assertEqual(os_mock.remove.mock_calls, [
            call('temp.txt'),
        ])


class RemoveFileContextManagerTestCase(unittest.TestCase):
    @patch('core.functions.os')
    def test_basic_operation(self, os_mock):

        path = '/tmp/temp.txt'
        with remove_file(path):
            pass

        self.assertEqual(os_mock.remove.mock_calls, [
            call(path),
        ])


class SendMailTestCase(unittest.TestCase):
    @patch('core.functions.send_mail_task')
    def test_no_recipients(self, task_mock):
        send_mail('Subject', 'Message', 'From', [])
        self.assertFalse(task_mock.delay.mock_calls)

    @patch('core.functions.send_mail_task')
    def test_task_case(self, task_mock):
        send_mail('Subject', 'Message', 'From', ['bob@example.com'],
                  reply_to='admin@example.com', defer=True)

        self.assertEqual(task_mock.delay.mock_calls, [
            call(body='Message', to=['bob@example.com'], from_email='From',
                 headers={'Reply-To': 'admin@example.com'}, subject='Subject'),
        ])

    @patch('core.functions.django.core.mail')
    def test_django_case(self, mail_mock):
        send_mail('Subject', 'Message', 'From', ['bob@example.com'],
                  reply_to='admin@example.com', defer=True)

        self.assertEqual(mail_mock.EmailMessage.mock_calls, [
            call(body='Message', to=['bob@example.com'], from_email='From',
                 headers={'Reply-To': 'admin@example.com'}, subject='Subject'),
            call().send(),
        ])


class EmailAdminsTestCase(unittest.TestCase):
    @patch('core.functions.send_mail')
    @patch('core.functions.settings')
    @patch('core.functions.Site.objects.get_current')
    def test_email_admins(self, current_mock, settings_mock, send_mail_mock):
        settings_mock.GPP_NO_REPLY_EMAIL = 'nope'
        settings_mock.ADMINS = [
            ('Alice', 'alice@example.com'),
            ('Bob', 'bob@example.com'),
        ]
        site_mock = Mock()
        site_mock.configure_mock(name='Site', domain='site.com')
        current_mock.return_value = site_mock

        email_admins(subject='Subject', message='Message')

        self.assertEqual(send_mail_mock.mock_calls, [
            call('[Site] Subject', 'Message', 'nope@site.com',
                 ['alice@example.com', 'bob@example.com']),
        ])


class EmailManagersTestCase(unittest.TestCase):
    @patch('core.functions.send_mail')
    @patch('core.functions.settings')
    @patch('core.functions.Site.objects.get_current')
    def test_email_admins(self, current_mock, settings_mock, send_mail_mock):
        settings_mock.GPP_NO_REPLY_EMAIL = 'nope'
        settings_mock.MANAGERS = [
            ('Alice', 'alice@example.com'),
            ('Bob', 'bob@example.com'),
        ]
        site_mock = Mock()
        site_mock.configure_mock(name='Site', domain='site.com')
        current_mock.return_value = site_mock

        email_managers(subject='Subject', message='Message')

        self.assertEqual(send_mail_mock.mock_calls, [
            call('[Site] Subject', 'Message', 'nope@site.com',
                 ['alice@example.com', 'bob@example.com']),
        ])


class GetFullNameTestCase(unittest.TestCase):
    def test_no_full_name(self):
        user = Mock()
        user.get_full_name.return_value = None
        user.username = 'pjmoto'

        name = get_full_name(user)

        self.assertEqual(name, 'pjmoto')

    def test_has_full_name(self):
        user = Mock()
        user.get_full_name.return_value = 'Paul'
        user.username = 'pjmoto'

        name = get_full_name(user)

        self.assertEqual(name, 'Paul')


class CopyrightStrTestCase(unittest.TestCase):
    def test_year_range(self):
        result = copyright_str()
        now = timezone.now()
        expected = 'Copyright (C) 2010 - {}, SurfGuitar101.com'.format(now.year)
        self.assertEqual(result, expected)


class GetIpTestCase(unittest.TestCase):
    def setUp(self):
        self.request = HttpRequest()

    def test_no_ip(self):
        ip = get_ip(self.request)
        self.assertIsNone(ip)

    def test_found_in_forwarded_for(self):
        self.request.META['HTTP_X_FORWARDED_FOR'] = '127.0.0.1'
        ip = get_ip(self.request)
        self.assertEqual(ip, '127.0.0.1')

    def test_found_in_remote_addr(self):
        self.request.META['REMOTE_ADDR'] = '127.0.0.1'
        ip = get_ip(self.request)
        self.assertEqual(ip, '127.0.0.1')

    def test_invalid_found_in_remote_addr(self):
        self.request.META['REMOTE_ADDR'] = 'xyz'
        ip = get_ip(self.request)
        self.assertIsNone(ip)

    def test_invalid_found_in_forwarded_for(self):
        self.request.META['HTTP_X_FORWARDED_FOR'] = '$%#!'
        ip = get_ip(self.request)
        self.assertIsNone(ip)


class IsAjaxTestCase(unittest.TestCase):
    def setUp(self):
        self.request = HttpRequest()

    def test_no_header(self):
        self.assertFalse(is_ajax(self.request))

    def test_header_present(self):
        self.request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.assertTrue(is_ajax(self.request))

    def test_other_value_is_not_ajax(self):
        self.request.META['HTTP_X_REQUESTED_WITH'] = 'fetch'
        self.assertFalse(is_ajax(self.request))

    def test_value_is_case_sensitive(self):
        self.request.META['HTTP_X_REQUESTED_WITH'] = 'xmlhttprequest'
        self.assertFalse(is_ajax(self.request))

    def test_matches_the_meta_key_it_replaced(self):
        """The header lookup must read the same value the removed
        HttpRequest.is_ajax() read out of META."""
        for value in ['XMLHttpRequest', 'xmlhttprequest', 'fetch', '', None]:
            request = HttpRequest()
            if value is not None:
                request.META['HTTP_X_REQUESTED_WITH'] = value
            old = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            self.assertEqual(is_ajax(request), old, msg=repr(value))


class GetPageTestCase(unittest.TestCase):
    def setUp(self):
        self.qdict = {}

    def test_valid_page(self):
        self.qdict = {'page': 42}
        result = get_page(self.qdict)
        self.assertEqual(result, 42)

    def test_page_not_found(self):
        result = get_page(self.qdict)
        self.assertEqual(result, 1)

    def test_invalid_page(self):
        self.qdict = {'page': 'wut'}
        result = get_page(self.qdict)
        self.assertEqual(result, 1)


class QuoteMessageTestCase(unittest.TestCase):
    def test_single_line(self):
        result = quote_message('pjmoto', 'I have a new album.')
        self.assertEqual(result, '*pjmoto wrote:*\n\n> I have a new album.\n\n')

    def test_multi_line(self):
        result = quote_message('pjmoto', 'I have a new album.\nAAA\nBBB\n')
        self.assertEqual(result,
                '*pjmoto wrote:*\n\n> I have a new album.\n> AAA\n> BBB\n\n')
