import datetime
import unittest

from PIL import Image

from mock import patch, call, Mock
from core.images import utils


class ParseImageTestCase(unittest.TestCase):
    @patch('core.images.utils.ImageFile')
    def test_parse_image(self, image_file_mock):
        file = Mock()
        file.chunks.return_value = ['a', 'b', 'c']

        result = utils.parse_image(file)

        self.assertEqual(image_file_mock.mock_calls, [
            call.Parser(),
            call.Parser().feed('a'),
            call.Parser().feed('b'),
            call.Parser().feed('c'),
            call.Parser().close(),
        ])
        self.assertEqual(result, image_file_mock.Parser().close())


class DownscaleTestCase(unittest.TestCase):
    def setUp(self):
        self.image = Mock()

    def test_will_not_upscale(self):
        self.image.size = (50, 50)
        result = utils.downscale_image_square(self.image, 100)
        self.assertEqual(result, self.image)
        self.assertListEqual(self.image.mock_calls, [])

    def test_downscale_square(self):
        self.image.size = (50, 50)
        result = utils.downscale_image_square(self.image, 25)

        self.assertEqual(result,
                         self.image.resize((25, 25), Image.ANTIALIAS))

    def test_downscale_wider(self):
        self.image.size = (500, 400)
        result = utils.downscale_image_square(self.image, 100)

        self.assertEqual(self.image.mock_calls, [
            call.crop((50, 0, 450, 400)),
            call.crop().resize((100, 100), Image.ANTIALIAS),
        ])
        self.assertEqual(result, self.image.crop().resize())

    def test_downscale_taller(self):
        self.image.size = (400, 500)
        result = utils.downscale_image_square(self.image, 100)

        self.assertEqual(self.image.mock_calls, [
            call.crop((0, 50, 400, 450)),
            call.crop().resize((100, 100), Image.ANTIALIAS),
        ])
        self.assertEqual(result, self.image.crop().resize())


class OrientImageTestCase(unittest.TestCase):
    def setUp(self):
        self.image = Mock()

    def test_has_no_exif_attribute(self):
        self.image = Mock(spec=Image)

        result = utils.orient_image(self.image)

        self.assertEqual(result, (False, self.image))
        self.assertEqual(self.image.mock_calls, [])

    def test_getexif_raises(self):
        attrs = {'_getexif.side_effect': IndexError}
        self.image.configure_mock(**attrs)

        result = utils.orient_image(self.image)

        self.assertEqual(result, (False, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
        ])

    def test_exif_has_no_orient_tag(self):
        attrs = {'_getexif.return_value': {}}
        self.image.configure_mock(**attrs)

        result = utils.orient_image(self.image)

        self.assertEqual(result, (False, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
        ])

    def test_exif_has_normal_orientation(self):
        attrs = {'_getexif.return_value': {0x112: 1}}
        self.image.configure_mock(**attrs)

        result = utils.orient_image(self.image)

        self.assertEqual(result, (False, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
        ])

    def test_exif_indicates_flipped_horizontal(self):
        attrs = {'_getexif.return_value': {0x112: 2}}
        self.image.configure_mock(**attrs)
        new_image = Mock()
        self.image.transpose.return_value = new_image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (True, new_image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
            call.transpose(Image.FLIP_LEFT_RIGHT),
        ])

    def test_exif_indicates_rotate_180(self):
        attrs = {'_getexif.return_value': {0x112: 3}}
        self.image.configure_mock(**attrs)
        new_image = Mock()
        self.image.transpose.return_value = new_image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (True, new_image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
            call.transpose(Image.ROTATE_180),
        ])

    def test_exif_indicates_mirror_vertical(self):
        attrs = {'_getexif.return_value': {0x112: 4}}
        self.image.configure_mock(**attrs)
        new_image = Mock()
        self.image.transpose.return_value = new_image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (True, new_image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
            call.transpose(Image.FLIP_TOP_BOTTOM),
        ])

    def test_exif_indicates_mirror_horiz_rotate_270(self):
        attrs = {'_getexif.return_value': {0x112: 5}}
        self.image.configure_mock(**attrs)
        self.image.transpose.return_value = self.image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (True, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
            call.transpose(Image.FLIP_LEFT_RIGHT),
            call.transpose(Image.ROTATE_90),
        ])

    def test_exif_indicates_rotate_90(self):
        attrs = {'_getexif.return_value': {0x112: 6}}
        self.image.configure_mock(**attrs)
        self.image.transpose.return_value = self.image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (True, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
            call.transpose(Image.ROTATE_270),
        ])

    def test_exif_indicates_mirror_horiz_rotate_90(self):
        attrs = {'_getexif.return_value': {0x112: 7}}
        self.image.configure_mock(**attrs)
        self.image.transpose.return_value = self.image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (True, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
            call.transpose(Image.FLIP_TOP_BOTTOM),
            call.transpose(Image.ROTATE_90),
        ])

    def test_exif_indicates_rotate_270(self):
        attrs = {'_getexif.return_value': {0x112: 8}}
        self.image.configure_mock(**attrs)
        self.image.transpose.return_value = self.image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (True, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
            call.transpose(Image.ROTATE_90),
        ])

    def test_exif_indicates_unknown_orientation(self):
        attrs = {'_getexif.return_value': {0x112: 42}}
        self.image.configure_mock(**attrs)
        self.image.transpose.return_value = self.image

        result = utils.orient_image(self.image)

        self.assertEqual(result, (False, self.image))
        self.assertEqual(self.image.mock_calls, [
            call._getexif(),
        ])
