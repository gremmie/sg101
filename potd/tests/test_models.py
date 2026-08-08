"""Tests for the POTD models, and specifically for thumbnail generation.

"""
import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from core.tests.images.imagemakers import jpeg_bytes, png_bytes
from potd.models import Photo


class GenerateThumbTestCase(TestCase):
    """Photo.generate_thumb() run against real image bytes.

    generate_thumb() reads image.format one line before it scales, and saves
    the thumbnail with the value it captured. scale_image() calls resize(),
    which returns a *new* image whose .format is None, so moving that capture
    below the scale leaves the save with no format at all. These tests fail if
    that happens, which is the only thing keeping the ordering from being tidied
    away by a later reader.

    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user('potd_user', 'p@example.com', 'pw')

    def _photo(self, name, data):
        return Photo(
            photo=SimpleUploadedFile(name, data),
            caption='caption',
            description='description',
            user=self.user)

    def _thumb_of(self, name, data):
        with override_settings(MEDIA_ROOT=self.media_root):
            photo = self._photo(name, data)
            photo.save()
            photo.thumb.open()
            try:
                image = Image.open(BytesIO(photo.thumb.read()))
                image.load()
            finally:
                photo.thumb.close()
        return image

    def test_thumbnail_of_a_jpeg_is_a_jpeg(self):
        thumb = self._thumb_of('potd.jpg', jpeg_bytes(size=(400, 300)))

        self.assertEqual(thumb.format, 'JPEG')
        self.assertEqual(thumb.size, (120, 90))

    def test_thumbnail_of_a_png_is_a_png_and_keeps_its_alpha(self):
        thumb = self._thumb_of('potd.png', png_bytes(size=(400, 300)))

        self.assertEqual(thumb.format, 'PNG')
        self.assertEqual(thumb.size, (120, 90))
        self.assertEqual(thumb.mode, 'RGBA')
        alpha = thumb.getchannel('A').getextrema()
        self.assertLess(alpha[0], alpha[1])

    def test_small_image_is_not_upscaled(self):
        thumb = self._thumb_of('small.png', png_bytes(size=(80, 60)))

        self.assertEqual(thumb.size, (80, 60))
