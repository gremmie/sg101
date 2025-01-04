"""
Tests for the forms in the user_photos application.
"""
from contextlib import contextmanager

import mock
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from user_photos.forms import HotLinkImageForm


@contextmanager
def fake_remove_file(path):
    yield path


class HotLinkImageFormTestCase(TestCase):

    def setUp(self):
        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.client.login(username=self.username, password=self.pw)

    @mock.patch('user_photos.forms.rate_limit_user')
    def test_no_url(self, rate_limit_mock):
        args = {}
        form = HotLinkImageForm(args, user=self.user)
        self.assertFalse(form.is_valid())

    @mock.patch('user_photos.forms.rate_limit_user')
    def test_bad_url(self, rate_limit_mock):
        args = {'url': 'jkdal;jkkls;$JSx49'}
        form = HotLinkImageForm(args, user=self.user)
        self.assertFalse(form.is_valid())

    @mock.patch('user_photos.forms.rate_limit_user')
    def test_rate_limit(self, rate_limit_mock):
        rate_limit_mock.side_effect = forms.ValidationError("Rate limit exceeded")
        args = {'url': 'http://example.com/a.jpg'}
        form = HotLinkImageForm(args, user=self.user)
        self.assertFalse(form.is_valid())

    @mock.patch('user_photos.forms.rate_limit_user')
    @mock.patch('user_photos.forms.download_file')
    @mock.patch('user_photos.forms.remove_file', new=fake_remove_file)
    @mock.patch('user_photos.forms.process_upload')
    def test_white_listed_url(self, upload_mock, dl_mock, rate_limit_mock):
        url = 'https://{}/a.jpg'.format(settings.USER_IMAGES_SOURCES[0])
        args = {'url': url}
        form = HotLinkImageForm(args, user=self.user)
        self.assertTrue(form.is_valid())
        result = form.save()
        self.assertEqual(result, url)
        self.assertFalse(dl_mock.called)
        self.assertFalse(upload_mock.called)

    @mock.patch('user_photos.forms.rate_limit_user')
    @mock.patch('user_photos.forms.download_file')
    @mock.patch('user_photos.forms.remove_file', new=fake_remove_file)
    @mock.patch('user_photos.forms.process_upload')
    def test_happy_path(self, upload_mock, dl_mock, rate_limit_mock):
        url = 'http://example.com/a.jpg'
        args = {'url': url}
        form = HotLinkImageForm(args, user=self.user)
        self.assertTrue(form.is_valid())
        new_url = 'https://img.example.com/a.jpg'
        upload_mock.return_value = (new_url, None)
        result = form.save()
        dl_mock.assert_called_once_with(url)
        self.assertEqual(result, new_url)

