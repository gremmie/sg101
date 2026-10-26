"""
Tests for the forms in the user_photos application.
"""
from contextlib import contextmanager

from unittest import mock

from PIL import UnidentifiedImageError
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from core.download import DownloadError, NotAccepted, Refused, TooLarge
from user_photos.forms import HotLinkError, HotLinkImageForm


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
        dl_mock.assert_called_once_with(url, timeout=10,
                                        max_bytes=10 * 1024 * 1024,
                                        accept='image/')
        self.assertEqual(result, new_url)


@mock.patch('user_photos.forms.rate_limit_user')
class HotLinkFailureTestCase(TestCase):
    """What a member is told when a hot-link cannot work.

    Measured from jaguar's logs before the cutover: 18 of 19 attempts failed,
    nearly all of them a YouTube or shop page pasted where an image address
    belongs, and every one reached the member as a server error.
    """

    def setUp(self):
        self.user = User.objects.create_user('test_user', '', 'password')

    def form(self, url='https://example.com/a.jpg'):
        form = HotLinkImageForm({'url': url}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        return form

    def test_youtube_links_are_refused_without_a_fetch(self, rate_limit_mock):
        for url in ('https://youtu.be/irzp0W_LG5g?si=x',
                    'https://www.youtube.com/watch?v=irzp0W_LG5g',
                    'https://m.youtube.com/watch?v=irzp0W_LG5g',
                    'https://youtube.com/shorts/abc'):
            with self.subTest(url=url):
                with mock.patch('user_photos.forms.download_file') as dl_mock:
                    form = HotLinkImageForm({'url': url}, user=self.user)
                    self.assertFalse(form.is_valid())
                    self.assertIn('Video Attachments', str(form.errors))
                    self.assertFalse(dl_mock.called)

    @mock.patch('user_photos.forms.download_file')
    def test_a_web_page_says_to_copy_the_image_address(self, dl_mock,
                                                        rate_limit_mock):
        dl_mock.side_effect = NotAccepted('text/html')
        with self.assertRaisesMessage(HotLinkError, 'Copy Image Address'):
            self.form().save()

    @mock.patch('user_photos.forms.download_file')
    def test_a_failed_fetch_says_so(self, dl_mock, rate_limit_mock):
        dl_mock.side_effect = DownloadError('404')
        with self.assertRaisesMessage(HotLinkError, "couldn't download"):
            self.form().save()

    @mock.patch('user_photos.forms.download_file')
    def test_a_refused_address_looks_like_any_failed_fetch(self, dl_mock,
                                                           rate_limit_mock):
        # Saying why would tell a prober which internal addresses exist.
        dl_mock.side_effect = Refused('10.0.0.1')
        with self.assertRaisesMessage(HotLinkError, "couldn't download"):
            self.form().save()

    @mock.patch('user_photos.forms.download_file')
    def test_too_large_says_so(self, dl_mock, rate_limit_mock):
        dl_mock.side_effect = TooLarge('big')
        with self.assertRaisesMessage(HotLinkError, '10 MB'):
            self.form().save()

    @mock.patch('user_photos.forms.download_file', return_value='/tmp/x.jpg')
    @mock.patch('user_photos.forms.remove_file', new=fake_remove_file)
    @mock.patch('user_photos.forms.process_upload')
    def test_an_unreadable_image_says_so(self, upload_mock, dl_mock,
                                         rate_limit_mock):
        upload_mock.side_effect = UnidentifiedImageError('cannot identify')
        with self.assertRaises(HotLinkError) as raised:
            self.form().save()
        self.assertIn("isn't an image", str(raised.exception))
        self.assertNotIn('/tmp', str(raised.exception))

    @mock.patch('user_photos.forms.download_file', return_value='/tmp/x.jpg')
    @mock.patch('user_photos.forms.remove_file', new=fake_remove_file)
    @mock.patch('user_photos.forms.process_upload')
    def test_an_unexpected_failure_is_not_disguised(self, upload_mock, dl_mock,
                                                   rate_limit_mock):
        upload_mock.side_effect = RuntimeError('S3 is down')
        with self.assertRaises(RuntimeError):
            self.form().save()

