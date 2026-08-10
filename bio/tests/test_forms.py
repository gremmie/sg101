"""
Form tests for the bio application.

"""
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from bio.forms import EditUserProfileForm
from bio.forms import SearchUsersForm
from bio.forms import UploadAvatarForm
from core.tests.images.imagemakers import jpeg_bytes, png_bytes


class EditUserProfileFormTestCase(TestCase):

    def test_valid_timezone(self):

        post_data = {'time_zone': 'US/Central'}
        form = EditUserProfileForm(post_data)
        self.assertTrue(form.is_valid())

    def test_invalid_timezone(self):

        post_data = {'time_zone': u'Am\xe9rica/Argentina_/_Buenos_Aires'}
        form = EditUserProfileForm(post_data)
        self.assertFalse(form.is_valid())

    def test_path_shaped_timezone_is_a_validation_error(self):
        """ZoneInfo answers path-shaped input with ValueError, not
        ZoneInfoNotFoundError. Catching only the latter would turn each of
        these into a 500 on a field anyone can post to."""

        for tz in ['../etc/passwd', '/etc/passwd', '..', 'a/../../b']:
            with self.subTest(tz=tz):
                form = EditUserProfileForm({'time_zone': tz})
                self.assertFalse(form.is_valid())

    def test_blank_timezone(self):

        form = EditUserProfileForm({})
        self.assertTrue(form.is_valid())

    def test_profile_text_good(self):
        post_data = {'profile_text': "This is my profile, no images."}
        form = EditUserProfileForm(post_data)
        self.assertTrue(form.is_valid())

    def test_profile_text_bad_image(self):
        post_data = {
            'profile_text': "I'm cool. ![image](http://example.com/test.jpg)",
        }
        form = EditUserProfileForm(post_data)
        self.assertFalse(form.is_valid())

    def test_signature_good(self):
        post_data = {'signature': "This is my signature, no images."}
        form = EditUserProfileForm(post_data)
        self.assertTrue(form.is_valid())

    def test_signature_bad_image(self):
        post_data = {
            'signature': "I'm cool. ![image](http://example.com/test.jpg)",
        }
        form = EditUserProfileForm(post_data)
        self.assertFalse(form.is_valid())


class SearchUsersFormTestCase(TestCase):

    def setUp(self):
        User.objects.create_user('BrianNeal', 'brianneal@example.com', 'pw')

    def test_exact_username(self):
        form = SearchUsersForm({'username': 'BrianNeal'})
        self.assertTrue(form.is_valid())

    def test_username_differing_case(self):
        # Members type a name into this box; matching it case-sensitively
        # would turn a found member into "does not exist".
        form = SearchUsersForm({'username': 'brianneal'})
        self.assertTrue(form.is_valid())

    def test_unknown_username(self):
        form = SearchUsersForm({'username': 'nobody'})
        self.assertFalse(form.is_valid())


class UploadAvatarFormTestCase(TestCase):
    """Avatar downscaling against real image bytes.

    clean_avatar_file() stashes self.file_type = image.format while the image
    is still the one it opened, because save() then scales through
    downscale_image_square(), whose crop()/resize() hand back new images with
    .format of None. Move that capture into save() and there is nothing left to
    read the format from, so these tests fail -- which is the point of them.

    """

    def _saved(self, name, data):
        upload = SimpleUploadedFile(name, data)
        form = UploadAvatarForm({}, {'avatar_file': upload})

        self.assertTrue(form.is_valid(), form.errors)

        filename, content = form.save()
        image = Image.open(BytesIO(content.read()))
        image.load()
        return filename, image

    def test_downscales_a_jpeg_avatar(self):
        filename, image = self._saved('avatar.jpg', jpeg_bytes(size=(400, 300)))

        self.assertEqual(filename, 'avatar.jpg')
        self.assertEqual(image.format, 'JPEG')
        self.assertEqual(image.size, (100, 100))

    def test_downscales_a_png_avatar_and_keeps_its_alpha(self):
        filename, image = self._saved('avatar.png', png_bytes(size=(400, 300)))

        self.assertEqual(filename, 'avatar.png')
        self.assertEqual(image.format, 'PNG')
        self.assertEqual(image.size, (100, 100))
        self.assertEqual(image.mode, 'RGBA')
        alpha = image.getchannel('A').getextrema()
        self.assertLess(alpha[0], alpha[1])

    def test_rejects_a_file_that_is_not_an_image(self):
        upload = SimpleUploadedFile('avatar.png', b'not an image')
        form = UploadAvatarForm({}, {'avatar_file': upload})

        self.assertFalse(form.is_valid())

    def test_small_avatar_is_returned_unchanged(self):
        data = png_bytes(size=(50, 50))
        upload = SimpleUploadedFile('small.png', data)
        form = UploadAvatarForm({}, {'avatar_file': upload})

        self.assertTrue(form.is_valid(), form.errors)
        filename, content = form.save()

        self.assertEqual(filename, 'small.png')
        self.assertIs(content, upload)
