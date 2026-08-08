"""Unit tests for the ssl_images management command."""
import os
import re
import shutil
import tempfile
import unittest
from urllib.parse import urlparse

import mock
from django.conf import settings
from PIL import Image

from core.management.commands.ssl_images import html_check
from core.management.commands.ssl_images import process_post, process_html
from core.management.commands.ssl_images import PHOTO_MAX_SIZE, resize_image
from core.tests.images.imagemakers import jpeg_bytes, png_bytes
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

        # This command reuses Markdown's internal IMAGE_LINK_RE. Markdown 2.6's
        # pattern no longer matches this malformed, nested-bracket markup (2.5's
        # did, and the old src then failed urlparse -> '{bad image}'), so
        # process_post now leaves the text untouched. Nothing is uploaded either
        # way, which is the behavior that actually matters for the migration.
        result = process_post(test_str)
        self.assertEqual(test_str, result)
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


class ProcessHtmlTestCase(unittest.TestCase):

    SG101_RE = re.compile(r'http://(?:www\.)?surfguitar101.com/', re.I)

    def setUp(self):
        self.assertTrue(len(settings.USER_IMAGES_SOURCES) > 0)
        self.safe_host = settings.USER_IMAGES_SOURCES[0]

    def tearDown(self):
        core.management.commands.ssl_images.url_cache = {}

    def test_empty_string(self):
        s = process_html('')
        self.assertEqual(s, '')

    def test_whitespace_string(self):
        s = process_html('\r\n\r\n')
        self.assertEqual(s, '')

    def test_no_matches(self):
        test_str = """<p>Here is a post that doesn't contain any image links at
        all. It also spans lines.</p>
        """
        result = process_html(test_str)
        self.assertEqual(test_str, result)

    def test_multiple_paragraphs(self):
        test_str = """<p>Here is a post that doesn't contain any image links at
        all. It also spans lines.</p>
        """
        test_str += test_str
        result = process_html(test_str)
        self.assertEqual(test_str, result)

    def test_sg101_images(self):
        test_str = """<p>An image:
        <img src="http://www.surfguitar101.com/img.jpg" alt="image">
        And another: <img src="HTTP://SURFGUITAR101.COM/foo/bar/img.png" alt="pic">
        More stuff here.</p>"""
        expected = self.SG101_RE.sub('/', test_str)
        result = process_html(test_str)
        self.assertNotEqual(test_str, expected)
        self.assertEqual(expected, result)

    def test_https_already(self):
        test_str = """<p>An image that is already using https:
            <img src="https://{}/zzz.png" alt="pic">
            It's cool.</p>""".format(self.safe_host)
        result = process_html(test_str)
        self.assertEqual(test_str, result)

    def test_https_sg101(self):
        test_str = """<p>An image that is already using https:
            <img src="https://www.SURFGUITAR101.com/zzz.png" alt="pic">
            It's cool.</p>
            """
        expected = """<p>An image that is already using https:
            <img src="/zzz.png" alt="pic">
            It's cool.</p>"""
        result = process_html(test_str)
        self.assertEqual(expected, result)

    def test_multiple_non_http(self):
        test_str = """<p>An image:
        <img src="http://www.surfguitar101.com/img.jpg" alt="pic">
        And another:
        <img src="HTTPS://{}/foo/bar/img.png" alt="stuff">
        More stuff here.</p>
        """.format(self.safe_host)
        expected = """<p>An image:
        <img src="/img.jpg" alt="pic">
        And another:
        <img src="HTTPS://{}/foo/bar/img.png" alt="stuff">
        More stuff here.</p>""".format(self.safe_host)
        result = process_html(test_str)
        self.assertEqual(expected, result)

    def test_https_already_with_title(self):
        test_str = """<p>An image that is already using https:
            <img src="https://{}/zzz.png" alt="1" title="the title">
            It's cool.</p>
            """.format(self.safe_host)
        result = process_html(test_str)
        self.assertEqual(test_str, result)

    @mock.patch('core.management.commands.ssl_images.save_image_to_cloud')
    def test_simple_replacement(self, upload_mock):
        old_src = 'http://example.com/images/my_image.jpg'
        new_src = 'https://cloud.com/ABCDEF.jpg'
        test_str = """<p>Here is a really cool http: based image:
            <img src="{}" alt="a">
            Cool, right?</p>""".format(old_src)
        expected = """<p>Here is a really cool http: based image:
            <img src="{}" alt="a">
            Cool, right?</p>""".format(new_src)

        upload_mock.return_value = new_src
        result = process_html(test_str)
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

        template = """<p>Here is a really cool http: based image:
            <img src="{}" alt="a">
            Cool, right?
            Another one: <img src="{}" alt="b">
            And finally
            <img src="{}" alt="c">
            </p>"""

        test_str = template.format(*old_src)
        expected = template.format(*new_src)

        upload_mock.side_effect = new_src
        result = process_html(test_str)
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

        template = """<p>Here is a really cool http: based image:
            <img src="{}" alt="a">
            Cool, right?
            Another two: <img src="{}" alt="b"><img src="{}" alt="c">
            And finally
            <img src="{}" alt="d"></p>"""

        test_str = template.format(*old_src)
        expected = template.format(*new_src)

        upload_mock.side_effect = new_src
        result = process_html(test_str)
        self.assertEqual(expected, result)
        upload_mock.assert_called_once_with(urlparse(old_src[0]))

    @mock.patch('core.management.commands.ssl_images.convert_to_ssl')
    def test_change_img_to_a(self, convert_mock):
        convert_mock.return_value = None
        test_str = """<p>A bad image:
            <img src="http://example.com/zzz.png" alt="1" title="the title">
            It's cool.</p>"""

        result = process_html(test_str)

        expected = """<p>A bad image:
            <a href="http://example.com/zzz.png">Image</a>
            It's cool.</p>"""
        self.assertEqual(result, expected)


class ResizeImageTestCase(unittest.TestCase):
    """resize_image() against real files on disk.

    This command rewrites images in place, and nothing else in the suite
    reaches its thumbnail() call -- reverting the resampling constant here left
    201 tests green while the command itself would raise AttributeError on the
    first oversized image it touched.

    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, name, data):
        path = os.path.join(self.tmpdir, name)
        with open(path, 'wb') as f:
            f.write(data)
        return path

    def test_oversized_image_is_resized_in_place(self):
        path = self._write('big.jpg', jpeg_bytes(size=(1000, 800)))

        self.assertTrue(resize_image(path))

        image = Image.open(path)
        self.assertEqual(image.size, (660, 528))
        self.assertLessEqual(image.size, PHOTO_MAX_SIZE)

    def test_oversized_png_keeps_its_format(self):
        path = self._write('big.png', png_bytes(size=(1000, 800)))

        self.assertTrue(resize_image(path))

        image = Image.open(path)
        self.assertEqual(image.size, (660, 528))
        self.assertEqual(image.format, 'PNG')

    def test_small_image_is_left_alone(self):
        data = jpeg_bytes(size=(320, 240))
        path = self._write('small.jpg', data)

        self.assertTrue(resize_image(path))

        with open(path, 'rb') as f:
            self.assertEqual(f.read(), data)

    def test_unreadable_file_reports_failure(self):
        path = self._write('junk.jpg', b'not an image at all')

        self.assertFalse(resize_image(path))
