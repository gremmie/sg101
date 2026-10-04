from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch, Mock

from core.functions import get_ip
from core.middleware import (InactiveUserMiddleware, RealClientIP,
                            WhosOnline)


class InactiveUserMiddlewareTestCase(TestCase):
    def setUp(self):
        factory = RequestFactory()
        self.request = factory.get('/contact')
        self.user = User.objects.create_user(username='pjmoto',
                                             email='member33@example.com',
                                             password='secret')
        # These tests call the middleware hooks directly, so get_response is
        # never invoked; it just has to be there.
        self.middleware = InactiveUserMiddleware(lambda request: HttpResponse())

    @patch('core.middleware.logout')
    def test_does_nothing_for_unauthed_user(self, mock_logout):
        self.request.user = AnonymousUser()
        self.middleware.process_view(self.request, lambda x: None, None, None)
        mock_logout.assert_not_called()

    @patch('core.middleware.logout')
    def test_does_nothing_for_active_user(self, mock_logout):
        self.user.is_active = True
        self.request.user = self.user
        self.middleware.process_view(self.request, lambda x: None, None, None)
        mock_logout.assert_not_called()

    @patch('core.middleware.logout')
    def test_logs_out_inactive_user(self, mock_logout):
        self.user.is_active = False
        self.request.user = self.user
        self.middleware.process_view(self.request, lambda x: None, None, None)
        mock_logout.assert_called_once_with(self.request)


class RealClientIPTestCase(TestCase):
    """The proxy's client address, carried across the hop to gunicorn.

    Apache's mod_remoteip rewrites REMOTE_ADDR from CF-Connecting-IP for
    connections out of Cloudflare's ranges, but the application no longer runs
    inside Apache: it is a separate process reached over the network, so what
    it sees as the peer is the proxy. The proxy restates the address it worked
    out in a header, and this puts it back where every reader already looks.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RealClientIP(lambda request: HttpResponse())

    def test_header_becomes_remote_addr(self):
        request = self.factory.get('/', REMOTE_ADDR='172.19.0.7',
                                   HTTP_X_REAL_IP='198.51.100.7')
        self.middleware(request)
        self.assertEqual(request.META['REMOTE_ADDR'], '198.51.100.7')

    def test_ipv6_header_becomes_remote_addr(self):
        request = self.factory.get('/', REMOTE_ADDR='172.19.0.7',
                                   HTTP_X_REAL_IP='2606:4700:4700::1111')
        self.middleware(request)
        self.assertEqual(request.META['REMOTE_ADDR'], '2606:4700:4700::1111')

    def test_no_header_leaves_remote_addr_alone(self):
        """Nothing but the proxy can reach the application, but a request that
        arrives without the header is not one to invent an address for."""
        request = self.factory.get('/', REMOTE_ADDR='172.19.0.7')
        self.middleware(request)
        self.assertEqual(request.META['REMOTE_ADDR'], '172.19.0.7')

    def test_an_address_that_is_not_one_is_refused(self):
        """The header is only as good as the proxy that set it. A value that
        is not an address is not written into REMOTE_ADDR, where six
        applications and the database's address columns would take it."""
        request = self.factory.get('/', REMOTE_ADDR='172.19.0.7',
                                   HTTP_X_REAL_IP='not-an-address')
        self.middleware(request)
        self.assertEqual(request.META['REMOTE_ADDR'], '172.19.0.7')

    def test_get_ip_reads_the_corrected_address(self):
        """The point of the exercise: the readers are unchanged and see the
        client, not the proxy."""
        request = self.factory.get('/', REMOTE_ADDR='172.19.0.7',
                                   HTTP_X_REAL_IP='198.51.100.7')
        self.middleware(request)
        self.assertEqual(get_ip(request), '198.51.100.7')

    def test_the_response_is_passed_through(self):
        response = HttpResponse('body')
        middleware = RealClientIP(lambda request: response)
        request = self.factory.get('/', REMOTE_ADDR='172.19.0.7')
        self.assertIs(middleware(request), response)


class WhosOnlineMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/contact')
        self.user = User.objects.create_user(username='pjmoto',
                                             email='member33@example.com',
                                             password='secret')
        self.middleware = WhosOnline(lambda request: HttpResponse())
        self.response = Mock()

    @patch('core.middleware.report_visitor')
    @patch('core.middleware.report_user')
    def test_does_nothing_when_no_user(self, mock_report_user,
                                       mock_report_visitor):
        result = self.middleware.process_response(self.request, self.response)
        self.assertEqual(result, self.response)
        self.response.assert_not_called()
        mock_report_visitor.assert_not_called()
        mock_report_user.assert_not_called()

    @patch('core.middleware.report_visitor')
    @patch('core.middleware.report_user')
    def test_does_nothing_when_ajax(self, mock_report_user,
                                    mock_report_visitor):
        ajax_request = self.factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ajax_request.user = self.user
        result = self.middleware.process_response(ajax_request, self.response)
        self.assertEqual(result, self.response)
        self.response.assert_not_called()
        mock_report_visitor.assert_not_called()
        mock_report_user.assert_not_called()

    @patch('core.middleware.report_visitor')
    @patch('core.middleware.report_user')
    def test_does_nothing_when_user_has_cookie(self, mock_report_user,
                                               mock_report_visitor):
        self.request.user = self.user
        self.request.COOKIES['sg101_online'] = 1
        result = self.middleware.process_response(self.request, self.response)
        self.assertEqual(result, self.response)
        self.response.assert_not_called()
        mock_report_visitor.assert_not_called()
        mock_report_user.assert_not_called()

    @patch('core.middleware.report_visitor')
    @patch('core.middleware.report_user')
    def test_reports_user(self, mock_report_user, mock_report_visitor):
        self.request.user = self.user
        result = self.middleware.process_response(self.request, self.response)
        self.assertEqual(result, self.response)
        self.response.set_cookie.assert_called_once_with(
                'sg101_online', '1', max_age=300)
        mock_report_visitor.assert_not_called()
        mock_report_user.assert_called_once_with('pjmoto')

    @patch('core.middleware.report_visitor')
    @patch('core.middleware.report_user')
    def test_does_nothing_when_visitor_no_cookies(self, mock_report_user,
                                                  mock_report_visitor):
        self.request.user = AnonymousUser()
        result = self.middleware.process_response(self.request, self.response)
        self.assertEqual(result, self.response)
        self.response.assert_not_called()
        mock_report_visitor.assert_not_called()
        mock_report_user.assert_not_called()

    @patch('core.middleware.report_visitor')
    @patch('core.middleware.report_user')
    def test_does_nothing_when_visitor_with_online_cookie(
            self, mock_report_user, mock_report_visitor):
        self.request.user = AnonymousUser()
        self.request.COOKIES = {
            settings.CSRF_COOKIE_NAME: 'deadbeef',
            'sg101_online': '1',
        }
        result = self.middleware.process_response(self.request, self.response)
        self.assertEqual(result, self.response)
        self.response.assert_not_called()
        mock_report_visitor.assert_not_called()
        mock_report_user.assert_not_called()

    @patch('core.middleware.get_ip')
    @patch('core.middleware.report_visitor')
    @patch('core.middleware.report_user')
    def test_reports_visitor(self, mock_report_user, mock_report_visitor,
                             mock_get_ip):
        self.request.user = AnonymousUser()
        self.request.COOKIES = {
            settings.CSRF_COOKIE_NAME: 'deadbeef',
        }
        mock_get_ip.return_value = '127.0.0.1'
        result = self.middleware.process_response(self.request, self.response)
        self.assertEqual(result, self.response)
        self.response.set_cookie.assert_called_once_with('sg101_online', '1',
                                                    max_age=300)
        mock_report_visitor.assert_called_once_with('127.0.0.1')
        mock_report_user.assert_not_called()
        mock_get_ip.assert_called_once_with(self.request)


class ReferrerPolicyTestCase(TestCase):
    """What the browser is told to send other sites about where it came from.

    YouTube refuses to play an embed that arrives with no Referer, showing a
    player error and nothing in the console. Django's default, same-origin,
    sends none to any other site; this is the browsers' own default, and what
    the site relied on before it sent a policy at all.
    """

    def test_other_sites_are_told_the_origin(self):
        response = self.client.get(reverse('contact-form'))
        self.assertEqual(response['Referrer-Policy'],
                         'strict-origin-when-cross-origin')
