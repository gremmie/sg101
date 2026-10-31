"""
Tests for the upload / gallery / delete views in the user_photos application.

The existing test_views module already exercises hotlink_image exhaustively;
these cover the remaining views. Real image processing and S3 traffic are mocked
at the same seams the app uses (the UploadForm and the delete_photos helper), so
the tests exercise the view logic without touching Pillow or Amazon.
"""
import json
import logging

from unittest import mock
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase
from django.test.utils import override_settings

from core.services import get_redis_connection
from core.tests.images.imagemakers import jpeg_bytes
from user_photos.models import Photo


AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


HEIC_MESSAGE = "HEIC photos aren't supported. Please choose a JPEG, PNG or GIF."


def ftyp(major, *compatible):
    """An ISO media file's first box: its size, 'ftyp', the major brand, a
    minor version, then the compatible brands."""
    body = b'ftyp' + major + b'\x00\x00\x00\x00' + b''.join(compatible)
    return (len(body) + 4).to_bytes(4, 'big') + body


def make_photo(user, url='https://s3.example.com/pic.jpg'):
    return Photo.objects.create(user=user, url=url,
                                thumb_url=url.replace('.jpg', '_thumb.jpg'),
                                signature='sig')


class UploadViewTests(TestCase):
    """The classic (non-ajax) upload form view."""

    def setUp(self):
        self.user = User.objects.create_user('uploader', '', 'pw')
        self.url = reverse('user_photos-upload')

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_renders_form_when_enabled(self):
        self.client.login(username='uploader', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['enabled'])
        self.assertIsNotNone(response.context['form'])

    @override_settings(USER_PHOTOS_ENABLED=False)
    def test_disabled_returns_503(self):
        self.client.login(username='uploader', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)

    @mock.patch('user_photos.views.UploadForm')
    def test_valid_post_redirects_to_new_photo(self, form_mock):
        self.client.login(username='uploader', password='pw')
        photo = make_photo(self.user)
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.return_value = photo

        response = self.client.post(self.url, {'photo': 'x'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], photo.get_absolute_url())

    @mock.patch('user_photos.views.UploadForm')
    def test_invalid_post_rerenders_form(self, form_mock):
        self.client.login(username='uploader', password='pw')
        form_mock.return_value.is_valid.return_value = False

        response = self.client.post(self.url, {'photo': 'x'})
        self.assertEqual(response.status_code, 200)


class UploadAjaxTests(TestCase):
    """The v2 ajax upload endpoint returns a JSON body with success/msg/url."""

    def setUp(self):
        self.user = User.objects.create_user('uploader', '', 'pw')
        self.url = reverse('user_photos-upload_ajax')

    def test_unauthenticated_is_forbidden(self):
        response = self.client.post(self.url, {}, **AJAX)
        self.assertEqual(response.status_code, 403)

    def test_non_ajax_is_not_allowed(self):
        self.client.login(username='uploader', password='pw')
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 405)

    @override_settings(USER_PHOTOS_ENABLED=False)
    def test_disabled_reports_failure(self):
        self.client.login(username='uploader', password='pw')
        response = self.client.post(self.url, {}, **AJAX)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertFalse(payload['success'])
        self.assertIn('disabled', payload['msg'])

    @mock.patch('user_photos.views.UploadForm')
    def test_valid_upload_reports_url(self, form_mock):
        self.client.login(username='uploader', password='pw')
        photo = make_photo(self.user)
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.return_value = photo

        response = self.client.post(self.url, {'photo': 'x'}, **AJAX)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['url'], photo.url)

    @mock.patch('user_photos.views.UploadForm')
    def test_invalid_upload_reports_failure(self, form_mock):
        self.client.login(username='uploader', password='pw')
        form_mock.return_value.is_valid.return_value = False
        form_mock.return_value.non_field_errors.return_value.as_text.return_value = ''
        form_mock.return_value.errors = {}

        response = self.client.post(self.url, {'photo': 'x'}, **AJAX)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertFalse(payload['success'])


class UploadAjaxV3Tests(TestCase):
    """The v3 ajax upload endpoint signals success/failure via status codes."""

    def setUp(self):
        self.user = User.objects.create_user('uploader', '', 'pw')
        self.url = reverse('user_photos-upload_ajax_v3')
        # A real form runs the real rate limit, whose counter lives a day in
        # the test redis. Start each test at zero and leave nothing behind.
        conn = get_redis_connection()
        quota_key = 'user_photos:counts:uploader'
        conn.delete(quota_key)
        self.addCleanup(conn.delete, quota_key)

    def test_unauthenticated_is_forbidden(self):
        response = self.client.post(self.url, {}, **AJAX)
        self.assertEqual(response.status_code, 403)

    def test_non_ajax_is_not_allowed(self):
        self.client.login(username='uploader', password='pw')
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 405)

    @override_settings(USER_PHOTOS_ENABLED=False)
    def test_disabled_returns_403(self):
        self.client.login(username='uploader', password='pw')
        response = self.client.post(self.url, {}, **AJAX)
        self.assertEqual(response.status_code, 403)

    @mock.patch('user_photos.views.UploadForm')
    def test_valid_upload_returns_200_with_url(self, form_mock):
        self.client.login(username='uploader', password='pw')
        photo = make_photo(self.user)
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.return_value = photo

        response = self.client.post(self.url, {'photo': 'x'}, **AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['url'], photo.url)

    @mock.patch('user_photos.views.UploadForm')
    def test_invalid_upload_returns_400(self, form_mock):
        self.client.login(username='uploader', password='pw')
        form_mock.return_value.is_valid.return_value = False
        form_mock.return_value.non_field_errors.return_value.as_text.return_value = ''
        form_mock.return_value.errors = {}

        response = self.client.post(self.url, {'photo': 'x'}, **AJAX)
        self.assertEqual(response.status_code, 400)

    @mock.patch('user_photos.views.UploadForm')
    def test_save_error_returns_500(self, form_mock):
        self.client.login(username='uploader', password='pw')
        form_mock.return_value.is_valid.return_value = True
        form_mock.return_value.save.side_effect = ValueError('boom')

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('user_photos.views', level='ERROR') as logged:
            response = self.client.post(self.url, {'photo': 'x'}, **AJAX)
        self.assertEqual(response.status_code, 500)
        # The exception can name a server path or an S3 detail; the member
        # gets a generic sentence and the operator the traceback.
        message = json.loads(response.content)['error_msg']
        self.assertTrue(message)
        self.assertNotIn('boom', message)
        self.assertIsNotNone(logged.records[0].exc_info)

    def test_a_file_that_is_not_an_image_says_why(self):
        """The commonest rejection. Its reason arrives in error_msg, as plain
        text: the post box shows it as text, so as_text()'s bullet would
        reach the member verbatim."""
        self.client.login(username='uploader', password='pw')
        not_an_image = SimpleUploadedFile('x.jpg', b'not an image',
                                          content_type='image/jpeg')

        response = self.client.post(self.url, {'image_file': not_an_image},
                                    **AJAX)
        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertEqual(payload, {'url': '', 'error_msg': payload['error_msg']})
        self.assertTrue(payload['error_msg'].startswith('Upload a valid image.'),
                        msg=payload['error_msg'])

    def post_unreadable(self, name, header):
        """Posts a file Pillow cannot read whose first bytes are header."""
        self.client.login(username='uploader', password='pw')
        upload = SimpleUploadedFile(name, header + b'\x00' * 64,
                                    content_type='application/octet-stream')
        response = self.client.post(self.url, {'image_file': upload}, **AJAX)
        self.assertEqual(response.status_code, 400)
        return json.loads(response.content)['error_msg']

    def test_a_heic_photo_is_named(self):
        """A HEIC is an image Pillow cannot read; saying it is not an image,
        or corrupt, would be wrong. Only the header matters, so these bytes
        need no encoder."""
        message = self.post_unreadable(
            'IMG_0001.HEIC', ftyp(b'heic', b'mif1', b'heic'))
        self.assertEqual(message, HEIC_MESSAGE)

    def test_a_heic_variant_brand_is_named(self):
        message = self.post_unreadable('IMG_0002.HEIC', ftyp(b'heix', b'mif1'))
        self.assertEqual(message, HEIC_MESSAGE)

    def test_heic_among_the_compatible_brands_is_named(self):
        message = self.post_unreadable('IMG_0003.HEIF', ftyp(b'mif1', b'heic'))
        self.assertEqual(message, HEIC_MESSAGE)

    def test_another_ftyp_file_is_not_called_heic(self):
        """AVIF shares the generic mif1 brand with HEIC."""
        message = self.post_unreadable('photo.avif', ftyp(b'avif', b'mif1', b'miaf'))
        self.assertTrue(message.startswith('Upload a valid image.'), msg=message)

    @override_settings(USER_PHOTOS_RATE_LIMIT=(0, 60))
    def test_over_quota_says_why(self):
        """The quota is a non-field error, raised from the form's clean(); a
        valid image makes it the only message."""
        self.client.login(username='uploader', password='pw')
        image = SimpleUploadedFile('x.jpg', jpeg_bytes(),
                                   content_type='image/jpeg')

        response = self.client.post(self.url, {'image_file': image}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content),
                         {'url': '',
                          'error_msg': "You've exceeded your upload quota. "
                                       "Please try again later."})

    @override_settings(USER_PHOTOS_ENABLED=False)
    def test_disabled_says_so(self):
        self.client.login(username='uploader', password='pw')
        response = self.client.post(self.url, {}, **AJAX)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content),
                         {'url': '',
                          'error_msg': 'Photo uploads are temporarily disabled'})


class GalleryAndDetailTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user('owner', '', 'pw')

    def test_gallery_requires_login(self):
        response = self.client.get(
            reverse('user_photos-gallery', kwargs={'username': 'owner'}))
        self.assertEqual(response.status_code, 302)

    def test_gallery_lists_owner_photos(self):
        make_photo(self.owner)
        self.client.login(username='owner', password='pw')
        response = self.client.get(
            reverse('user_photos-gallery', kwargs={'username': 'owner'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['photos']),
                         list(Photo.objects.filter(user=self.owner)))
        self.assertEqual(response.context['gallery_owner'], self.owner)

    def test_gallery_owner_differing_case(self):
        make_photo(self.owner)
        self.client.login(username='owner', password='pw')
        response = self.client.get(
            reverse('user_photos-gallery', kwargs={'username': 'OWNER'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['gallery_owner'], self.owner)

    def test_gallery_unknown_user_is_404(self):
        self.client.login(username='owner', password='pw')
        response = self.client.get(
            reverse('user_photos-gallery', kwargs={'username': 'nobody'}))
        self.assertEqual(response.status_code, 404)

    def test_photo_detail_renders(self):
        photo = make_photo(self.owner)
        response = self.client.get(photo.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['photo'], photo)


class DeleteViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('owner', '', 'pw')
        self.other = User.objects.create_user('other', '', 'pw')
        self.url = reverse('user_photos-delete')

    def test_delete_requires_login(self):
        response = self.client.post(self.url, {'photo_id': ['1']})
        self.assertEqual(response.status_code, 302)

    def test_delete_requires_post(self):
        self.client.login(username='owner', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @override_settings(USER_PHOTOS_ENABLED=False)
    def test_disabled_redirects_without_deleting(self):
        photo = make_photo(self.user)
        self.client.login(username='owner', password='pw')
        response = self.client.post(self.url, {'photo_id': [str(photo.pk)]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Photo.objects.filter(pk=photo.pk).exists())

    @mock.patch('user_photos.views.delete_photos')
    def test_owner_can_delete_own_photos(self, delete_mock):
        photo = make_photo(self.user)
        self.client.login(username='owner', password='pw')

        response = self.client.post(self.url, {'photo_id': [str(photo.pk)]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(delete_mock.called)
        self.assertFalse(Photo.objects.filter(pk=photo.pk).exists())

    @mock.patch('user_photos.views.delete_photos')
    def test_cannot_delete_another_users_photo(self, delete_mock):
        victim_photo = make_photo(self.other)
        self.client.login(username='owner', password='pw')

        response = self.client.post(self.url, {'photo_id': [str(victim_photo.pk)]})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(delete_mock.called)
        self.assertTrue(Photo.objects.filter(pk=victim_photo.pk).exists())

    @mock.patch('user_photos.views.delete_photos')
    def test_non_integer_photo_id_is_ignored(self, delete_mock):
        self.client.login(username='owner', password='pw')
        response = self.client.post(self.url, {'photo_id': ['not-a-number']})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(delete_mock.called)
