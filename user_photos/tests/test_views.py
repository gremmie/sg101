"""
Tests for the views in the user_photos application.

"""
import json
import logging

from unittest import mock
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse

from core.services import get_redis_connection
from user_photos.forms import HotLinkError


class HotlinkImageTestCase(TestCase):

    def setUp(self):
        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username, password=self.pw))
        self.view_url = reverse('user_photos-hotlink')
        # A real form runs the real rate limit, whose counter lives a day in
        # the test redis. Start each test at zero and leave nothing behind.
        conn = get_redis_connection()
        quota_key = 'user_photos:counts:' + self.username
        conn.delete(quota_key)
        self.addCleanup(conn.delete, quota_key)

    def testUnauthenticatedUser(self):
        self.client.logout()
        response = self.client.post(self.view_url,
                                    {'url': 'http://example.com/test.jpg'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 403)

    def testWrongMethod(self):
        response = self.client.get(self.view_url)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 405)

    def testNotAjax(self):
        response = self.client.post(self.view_url,
                                    {'url': 'http://example.com/test.jpg'})
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 405)

    @override_settings(USER_PHOTOS_ENABLED=False)
    def testServiceDisabled(self):
        response = self.client.post(self.view_url,
                                    {'url': 'http://example.com/test.jpg'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 403)

    @mock.patch('user_photos.views.HotLinkImageForm')
    def testFormInvalid(self, form_mock):
        form_mock.return_value.is_valid.return_value = False
        form_mock.return_value.non_field_errors.return_value = mock.Mock()
        form_mock.return_value.non_field_errors.return_value.as_text.return_value = 'bad stuff'
        form_mock.return_value.errors.return_value = {}

        response = self.client.post(self.view_url,
                                    {'url': 'http://example.com/test.jpg'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 400)

    def testFormErrorsReachTheMemberAsPlainText(self):
        # The clients put error_msg into an alert and into .text(), so it must
        # be the message itself: as_text() escaped the apostrophes (&#x27;)
        # and prefixed a '* ' bullet.
        from user_photos.forms import YOUTUBE_MESSAGE
        response = self.client.post(self.view_url,
                                    {'url': 'https://youtu.be/irzp0W_LG5g'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['error_msg'],
                         YOUTUBE_MESSAGE)

    @mock.patch('user_photos.views.HotLinkImageForm')
    def testHappyPath(self, form_mock):
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.return_value = 'https://example.com/a.jpg'

        response = self.client.post(self.view_url,
                                    {'url': 'http://example.com/test.jpg'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)
        expected = {"url": "https://example.com/a.jpg", "error_msg": ""}
        actual = json.loads(response.content)
        self.assertEqual(actual, expected)

    @mock.patch('user_photos.views.HotLinkImageForm')
    def testFormSaveRaises(self, form_mock):
        # An unexpected failure is still a 500, but the member is not shown
        # the exception's text -- it named a server temp path -- and the
        # operator gets a traceback, which the old blanket except threw away.
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.side_effect = ValueError('/tmp/tmp91ql7xcl.html')

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('user_photos.views', level='ERROR') as logged:
            response = self.client.post(self.view_url,
                                        {'url': 'http://example.com/test.jpg'},
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 500)
        message = json.loads(response.content)['error_msg']
        self.assertTrue(message)
        self.assertNotIn('/tmp', message)
        self.assertIsNotNone(logged.records[0].exc_info)

    @mock.patch('user_photos.views.HotLinkImageForm')
    def testHotLinkErrorIsTheMembersMistake(self, form_mock):
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.side_effect = HotLinkError('Not an image.')

        response = self.client.post(self.view_url,
                                    {'url': 'http://example.com/page'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content),
                         {'url': '', 'error_msg': 'Not an image.'})
