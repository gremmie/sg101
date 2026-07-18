"""
Tests for the views in the user_photos application.

"""
import json

import mock
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse


class HotlinkImageTestCase(TestCase):

    def setUp(self):
        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username, password=self.pw))
        self.view_url = reverse('user_photos-hotlink')

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
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.side_effect = ValueError

        response = self.client.post(self.view_url,
                                    {'url': 'http://example.com/test.jpg'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 500)
