"""Image tests that use a real PIL.Image rather than a Mock.

The neighbouring modules patch PIL out entirely. That makes them fast, but it
also means they cannot fail when PIL changes underneath: a Mock returns an
attribute whatever it is called, so an assertion naming a constant that has been
removed keeps passing while the real code raises AttributeError. These tests run
real bytes through the real library, so they fail when that happens.

"""
import os
import shutil
import tempfile
import unittest
from io import BytesIO

from django.test import TestCase, override_settings
from PIL import Image

from core.images.upload import process_upload
from core.images.utils import downscale_image_square, orient_image, parse_image
from core.tests.images.imagemakers import (gif_bytes, jpeg_bytes, opened,
                                           oriented_jpeg_bytes, png_bytes)


class _File(object):
    """The part of a Django uploaded file that parse_image() uses."""

    def __init__(self, data):
        self.data = data

    def chunks(self):
        yield self.data


class DownscaleRealImageTestCase(unittest.TestCase):
    """downscale_image_square() against real pixels.

    This is the test that fails if Image.Resampling.LANCZOS is reverted to
    Image.ANTIALIAS: the constant is gone from Pillow 10 onwards, so the call
    raises AttributeError instead of quietly resampling.

    """

    def test_downscales_a_jpeg(self):
        image = downscale_image_square(opened(jpeg_bytes()), 100)

        self.assertEqual(image.size, (100, 100))
        self.assertEqual(image.mode, 'RGB')

    def test_downscales_a_png_and_keeps_its_alpha(self):
        image = downscale_image_square(opened(png_bytes()), 100)

        self.assertEqual(image.size, (100, 100))
        self.assertEqual(image.mode, 'RGBA')
        # An alpha ramp survives as a range of values; a flattened image would
        # report a single one.
        alpha = image.getchannel('A').getextrema()
        self.assertLess(alpha[0], alpha[1])

    def test_downscales_a_gif(self):
        image = downscale_image_square(opened(gif_bytes()), 100)

        self.assertEqual(image.size, (100, 100))

    def test_resamples_rather_than_dropping_pixels(self):
        """LANCZOS averages neighbours; NEAREST just picks one.

        Without this, a resize that had silently fallen back to nearest
        neighbour would still satisfy every size assertion above.

        """
        source = opened(jpeg_bytes())

        lanczos = downscale_image_square(source, 100)
        nearest = source.crop((50, 0, 350, 300)).resize(
            (100, 100), Image.Resampling.NEAREST)

        self.assertNotEqual(lanczos.tobytes(), nearest.tobytes())

    def test_will_not_upscale(self):
        source = opened(jpeg_bytes(size=(50, 50)))

        self.assertIs(downscale_image_square(source, 100), source)


class ProcessUploadRealImageTestCase(TestCase):
    """process_upload() run against a real file on disk.

    The other tests of this module patch core.images.upload.Image wholesale, so
    the resampling constant they assert on is a Mock attribute: reverting the
    four thumbnail() calls to Image.ANTIALIAS *and* the assertions to match
    leaves that suite green while a real upload raises AttributeError. Nothing
    else exercises these four call sites against PIL, so this does.

    """

    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.upload_dir = 'user_upload'
        os.makedirs(os.path.join(self.media_root, self.upload_dir))
        self.source_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.media_root, ignore_errors=True)
        shutil.rmtree(self.source_dir, ignore_errors=True)

    def _upload(self, name, data):
        path = os.path.join(self.source_dir, name)
        with open(path, 'wb') as f:
            f.write(data)

        with override_settings(MEDIA_ROOT=self.media_root,
                               USER_PHOTOS_LOCAL_UPLOAD=True,
                               USER_PHOTOS_LOCAL_UPLOAD_DIR=self.upload_dir):
            url, thumb_url = process_upload(None, path)

        directory = os.path.join(self.media_root, self.upload_dir)
        written = sorted(os.listdir(directory))
        images = [Image.open(os.path.join(directory, n)) for n in written]
        for image in images:
            image.load()
        return url, thumb_url, images

    def test_uploaded_jpeg_is_resized_and_thumbnailed(self):
        url, thumb_url, images = self._upload(
            'photo.jpg', jpeg_bytes(size=(1000, 800)))

        self.assertTrue(url.endswith('.jpg'))
        self.assertTrue(thumb_url.endswith('t.jpg'))
        # The full image is capped at USER_PHOTOS_MAX_SIZE and the thumbnail at
        # USER_PHOTOS_THUMB_SIZE, both preserving aspect ratio.
        self.assertEqual(sorted(i.size for i in images),
                         [(120, 96), (660, 528)])
        self.assertEqual({i.format for i in images}, {'JPEG'})

    def test_uploaded_png_keeps_its_format_and_alpha(self):
        """The thumbnail is saved with format=image.format.

        thumbnail() scales in place and so keeps .format, which is the only
        reason that save works. A PNG is the case that shows it: written with
        no format at all, the save raises rather than guessing.

        """
        url, thumb_url, images = self._upload(
            'photo.png', png_bytes(size=(1000, 800)))

        self.assertEqual(sorted(i.size for i in images),
                         [(120, 96), (660, 528)])
        self.assertEqual({i.format for i in images}, {'PNG'})
        for image in images:
            self.assertEqual(image.mode, 'RGBA')
            alpha = image.getchannel('A').getextrema()
            self.assertLess(alpha[0], alpha[1])

    def test_uploaded_image_is_oriented_from_its_exif(self):
        url, thumb_url, images = self._upload(
            'turned.jpg', oriented_jpeg_bytes(orientation=6, size=(1000, 800)))

        # Orientation 6 is "rotate 90 CW", so the portrait result is taller
        # than it is wide -- the landscape source was 1000x800.
        for image in images:
            self.assertGreater(image.size[1], image.size[0])


class FormatAfterScalingTestCase(unittest.TestCase):
    """Lock down the .format behaviour two call sites are built around.

    potd.models.Photo.generate_thumb() and bio.forms.UploadAvatarForm both
    capture image.format one line *before* they scale, because the scaling
    helpers return new images that have lost it. That ordering looks arbitrary
    and is one tidy-up away from breaking, so the contract it depends on is
    asserted here rather than left to the next reader to rediscover.

    """

    def setUp(self):
        self.image = opened(png_bytes())

    def test_open_populates_format(self):
        self.assertEqual(self.image.format, 'PNG')

    def test_crop_returns_a_new_image_without_format(self):
        self.assertIsNone(self.image.crop((0, 0, 100, 100)).format)

    def test_resize_returns_a_new_image_without_format(self):
        resized = self.image.resize((100, 100), Image.Resampling.LANCZOS)

        self.assertIsNone(resized.format)

    def test_thumbnail_scales_in_place_and_keeps_format(self):
        self.image.thumbnail((100, 100), Image.Resampling.LANCZOS)

        self.assertEqual(self.image.format, 'PNG')

    def test_saving_with_a_lost_format_is_what_breaks(self):
        """The failure the two captures exist to prevent."""
        resized = self.image.resize((100, 100), Image.Resampling.LANCZOS)

        with self.assertRaises(Exception):
            resized.save(BytesIO(), resized.format)


class ParseImageRealFileTestCase(unittest.TestCase):

    def test_parses_a_png_and_reports_its_format(self):
        image = parse_image(_File(png_bytes()))

        self.assertEqual(image.format, 'PNG')
        self.assertEqual(image.mode, 'RGBA')

    def test_parses_a_jpeg_and_reports_its_format(self):
        image = parse_image(_File(jpeg_bytes()))

        self.assertEqual(image.format, 'JPEG')

    def test_garbage_raises_something_the_avatar_form_catches(self):
        """bio.forms.UploadAvatarForm catches IOError around this call."""
        with self.assertRaises(IOError):
            parse_image(_File(b'this is not an image'))


class OrientRealImageTestCase(unittest.TestCase):

    def test_rotates_a_jpeg_carrying_orientation_6(self):
        image = opened(oriented_jpeg_bytes(orientation=6, size=(400, 300)))

        changed, oriented = orient_image(image)

        self.assertTrue(changed)
        self.assertEqual(oriented.size, (300, 400))

    def test_leaves_an_image_without_exif_alone(self):
        image = opened(png_bytes())

        changed, oriented = orient_image(image)

        self.assertFalse(changed)
        self.assertIs(oriented, image)
