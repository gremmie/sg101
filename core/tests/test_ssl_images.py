"""Unit tests for the ssl_images management command."""
import re
import unittest

import mock

from core.management.commands.ssl_images import process_post


class ProcessPostTestCase(unittest.TestCase):

    SG101_RE = re.compile(r'http://(?:www\.)?surfguitar101.com/', re.I)

    def test_empty_string(self):
        s = process_post('')
        self.assertEqual(s, '')

    def test_no_matches(self):
        test_str = """Here is a post that doesn't contain any image links at
        all. It also spans lines.
        """
        result = process_post(test_str)
        self.assertEqual(test_str, result)

    def test_sg101_images(self):
        test_str = """An image: ![image](http://www.surfguitar101.com/img.jpg)
        And another: ![pic](HTTP://SURFGUITAR101.COM/foo/bar/img.png).
        More stuff here."""
        expected = self.SG101_RE.sub('/', test_str)
        result = process_post(test_str)
        self.assertNotEqual(test_str, expected)
        self.assertEqual(expected, result)

    def test_sg101_with_newlines(self):
        test_str = """An image: ![image](
http://surfguitar101.com/media/zzz.jpg
)
    with trailing text."""
        expected = """An image: ![image](/media/zzz.jpg)
    with trailing text."""
        result = process_post(test_str)
        self.assertNotEqual(test_str, expected)
        self.assertEqual(expected, result)

    def test_https_already(self):
        test_str = """An image that is already using https:
            ![flyer](https://example.com/zzz.png)
            It's cool.
            """
        result = process_post(test_str)
        self.assertEqual(test_str, result)

    def test_https_sg101(self):
        test_str = """An image that is already using https:
            ![flyer](https://www.SURFGUITAR101.com/zzz.png)
            It's cool.
            """
        expected = """An image that is already using https:
            ![flyer](/zzz.png)
            It's cool.
            """
        result = process_post(test_str)
        self.assertEqual(expected, result)

    def test_multiple_non_http(self):
        test_str = """An image: ![image](http://www.surfguitar101.com/img.jpg)
        And another: ![pic](HTTPS://example.com/foo/bar/img.png).
        More stuff here."""
        expected = """An image: ![image](/img.jpg)
        And another: ![pic](HTTPS://example.com/foo/bar/img.png).
        More stuff here."""
        result = process_post(test_str)
        self.assertEqual(expected, result)

    def test_https_already_with_title(self):
        test_str = """An image that is already using https:
            ![flyer](https://example.com/zzz.png "the title")
            It's cool.
            """
        result = process_post(test_str)
        self.assertEqual(test_str, result)

    def test_sg101_with_title(self):
        test_str = """An image on SG101:
            ![flyer](http://surfguitar101.com/zzz.png "the title")
            It's cool.
            """
        expected = """An image on SG101:
            ![flyer](/zzz.png "the title")
            It's cool.
            """
        result = process_post(test_str)
        self.assertEqual(expected, result)

    def test_https_sg101_brackets(self):
        test_str = """An image that is already using https:
            ![flyer](<https://www.SURFGUITAR101.com/zzz.png>)
            It's cool.
            """
        expected = """An image that is already using https:
            ![flyer](/zzz.png)
            It's cool.
            """
        result = process_post(test_str)
        self.assertEqual(expected, result)

    def test_https_already_brackets(self):
        test_str = """An image that is already using https:
            ![flyer](<https://example.com/zzz.png>)
            It's cool.
            """
        expected = """An image that is already using https:
            ![flyer](https://example.com/zzz.png)
            It's cool.
            """
        result = process_post(test_str)
        self.assertEqual(expected, result)

    @mock.patch('core.management.commands.ssl_images.save_image_to_cloud')
    def test_simple_replacement(self, upload_mock):
        old_src = 'http://example.com/images/my_image.jpg'
        new_src = 'https://cloud.com/ABCDEF.jpg'
        test_str = """Here is a really cool http: based image:
            ![flyer]({})
            Cool, right?""".format(old_src)
        expected = """Here is a really cool http: based image:
            ![flyer]({})
            Cool, right?""".format(new_src)

        upload_mock.return_value = new_src
        result = process_post(test_str)
        self.assertEqual(expected, result)
        upload_mock.assert_called_once_with(old_src)

    @mock.patch('core.management.commands.ssl_images.save_image_to_cloud')
    def test_multiple_replacement(self, upload_mock):
        old_src = [
            'http://example.com/images/my_image.jpg',
            'http://example.com/static/wow.gif',
            'http://example.com/media/a/b/c/pic.png',
        ]
        new_src = [
            'https://cloud.com/some/path/012345.jpg',
            'https://cloud.com/some/path/6789AB.gif',
            'https://cloud.com/some/path/CDEF01.png',
        ]

        template = """Here is a really cool http: based image:
            ![flyer]({})
            Cool, right?
            Another one: ![pic]({})
            And finally
            ![an image]({})
            """

        test_str = template.format(*old_src)
        expected = template.format(*new_src)

        upload_mock.side_effect = new_src
        result = process_post(test_str)
        self.assertEqual(expected, result)
        expected_args = [mock.call(c) for c in old_src]
        self.assertEqual(upload_mock.call_args_list, expected_args)

    @mock.patch('core.management.commands.ssl_images.save_image_to_cloud')
    def test_multiple_replacement_2(self, upload_mock):
        old_src = [
            'http://example.com/images/my_image.jpg',
            'https://example.com/static/wow.gif',
            'http://www.surfguitar101.com/media/a/b/c/pic.png',
            'http://surfguitar101.com/media/a/b/c/pic2.png',
        ]
        new_src = [
            'https://cloud.com/some/path/012345.jpg',
            'https://example.com/static/wow.gif',
            '/media/a/b/c/pic.png',
            '/media/a/b/c/pic2.png',
        ]

        template = """Here is a really cool http: based image:
            ![flyer]({})
            Cool, right?
            Another two: ![pic]({})  ![photo]({})
            And finally
            ![an image]({}).
            """

        test_str = template.format(*old_src)
        expected = template.format(*new_src)

        upload_mock.side_effect = new_src
        result = process_post(test_str)
        self.assertEqual(expected, result)
        upload_mock.assert_called_once_with(old_src[0])
