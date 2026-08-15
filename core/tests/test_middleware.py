from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from unittest.mock import patch, Mock

from core.middleware import InactiveUserMiddleware, WhosOnline


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
