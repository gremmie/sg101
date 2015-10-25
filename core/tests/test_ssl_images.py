"""Unit tests for the ssl_images management command."""
import re
import unittest
from urlparse import urlparse

import mock
from django.conf import settings

from core.management.commands.ssl_images import html_check
from core.management.commands.ssl_images import process_post
import core.management.commands.ssl_images


class ProcessPostTestCase(unittest.TestCase):

    SG101_RE = re.compile(r'http://(?:www\.)?surfguitar101.com/', re.I)

    def setUp(self):
        self.assertTrue(len(settings.USER_IMAGES_SOURCES) > 0)
        self.safe_host = settings.USER_IMAGES_SOURCES[0]

    def tearDown(self):
        core.management.commands.ssl_images.url_cache = {}

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
            ![flyer](https://{}/zzz.png)
            It's cool.
            """.format(self.safe_host)
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
        And another: ![pic](HTTPS://{}/foo/bar/img.png).
        More stuff here.""".format(self.safe_host)
        expected = """An image: ![image](/img.jpg)
        And another: ![pic](HTTPS://{}/foo/bar/img.png).
        More stuff here.""".format(self.safe_host)
        result = process_post(test_str)
        self.assertEqual(expected, result)

    def test_https_already_with_title(self):
        test_str = """An image that is already using https:
            ![flyer](https://{}/zzz.png "the title")
            It's cool.
            """.format(self.safe_host)
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
            ![flyer](<https://{}/zzz.png>)
            It's cool.
            """.format(self.safe_host)
        expected = """An image that is already using https:
            ![flyer](https://{}/zzz.png)
            It's cool.
            """.format(self.safe_host)
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
        upload_mock.assert_called_once_with(urlparse(old_src))

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
        expected_args = [mock.call(urlparse(c)) for c in old_src]
        self.assertEqual(upload_mock.call_args_list, expected_args)

    @mock.patch('core.management.commands.ssl_images.save_image_to_cloud')
    def test_multiple_replacement_2(self, upload_mock):
        old_src = [
            'http://example.com/images/my_image.jpg',
            'https://{}/static/wow.gif'.format(self.safe_host),
            'http://www.surfguitar101.com/media/a/b/c/pic.png',
            'http://surfguitar101.com/media/a/b/c/pic2.png',
        ]
        new_src = [
            'https://cloud.com/some/path/012345.jpg',
            'https://{}/static/wow.gif'.format(self.safe_host),
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
        upload_mock.assert_called_once_with(urlparse(old_src[0]))

    @mock.patch('core.management.commands.ssl_images.save_image_to_cloud')
    def test_caching(self, upload_mock):
        old_src = [
            'http://example.com/images/my_image.jpg',
            'http://example.com/static/wow.gif',
            'http://example.com/images/my_image.jpg',
        ]
        new_src = [
            'https://cloud.com/some/path/012345.jpg',
            'https://cloud.com/some/path/6789AB.gif',
            'https://cloud.com/some/path/012345.jpg',
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
        expected_args = [mock.call(urlparse(c)) for c in old_src[:2]]
        self.assertEqual(upload_mock.call_args_list, expected_args)

    @mock.patch('core.management.commands.ssl_images.save_image_to_cloud')
    def test_bad_image_url(self, upload_mock):
        test_str = u'![image](http://[url=http://www.flickr.com/photos/85447101@N04/8025176073/][img]http://farm9.staticflickr.com/8456/8025176073_91ac0c3d18_b.jpg[/img][/url] [url=http://www.flickr.com/photos/85447101@N04/8025176073/]IMG_0398[/url] by [url=http://www.flickr.com/people/85447101@N04/]friendshipmaster[/url], on Flick)'
        expected = u'{bad image}'

        result = process_post(test_str)
        self.assertEqual(expected, result)
        self.assertEqual(upload_mock.call_count, 0)


class HtmlCheckTestCase(unittest.TestCase):

    def test_empty(self):
        self.assertFalse(html_check(''))

    def test_no_images(self):
        self.assertFalse(html_check('<p>Hi there!</p>'))
        self.assertFalse(html_check('<p>Hi <b>there</b>!</p>'))

    def test_safe_image(self):
        self.assertFalse(html_check('<img src="https://a.jpg" />'))
        self.assertFalse(html_check('<img src="" alt="stuff" />'))
        self.assertFalse(html_check('<img src="HTTPS://a.jpg" />'))
        self.assertFalse(html_check("""
            <div>
            <p>Look: <img src="https://a.jpg" alt="a" /></p>
            <p>Look again: <img src="https://b.jpg" alt="b" /></p>
            </div>
            """))

    def test_one_image(self):
        self.assertTrue(html_check('<img src="http://a.jpg" alt="a" />'))
        self.assertTrue(html_check(
            '<p>Look: <img src="http://a.jpg" alt="a" /></p>'))

    def test_two_images(self):
        self.assertTrue(html_check("""
            <p>Look: <img src="https://a.jpg" alt="a" /></p>
            <p>Look again: <img src="http://b.jpg" alt="b" /></p>
            """))
        self.assertTrue(html_check("""
            <p>Look: <img src="http://a.jpg" alt="a" /></p>
            <p>Look again: <img src="http://b.jpg" alt="b" /></p>
            """))
        self.assertTrue(html_check("""
            <div>
            <p>Look: <img src="http://a.jpg" alt="a" /></p>
            <p>Look again: <img src="http://b.jpg" alt="b" /></p>
            </div>
            """))
        self.assertTrue(html_check("""
            <div>
            <p>Look: <img src="http://a.jpg" alt="a" /></p>
            <p>Look again: <img src="https://b.jpg" alt="b" /></p>
            </div>
            """))
