"""Tests for the core.html module."""
import unittest

from core.html import ImageCheckError
from core.html import image_check


TEST_HTML = """
<p>Posters and Facebook events are starting to come in...</p>
<p><img src="{src1}" alt="image"></p>
<p><img src="{src2}" alt="image"></p>
"""


class ImageCheckTestCase(unittest.TestCase):
    def setUp(self):
        self.allowed_hosts = ['example.com']

    def test_happy_path(self):
        url1 = 'https://example.com/1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        result = image_check(html, self.allowed_hosts)
        self.assertTrue(result)

    def test_empty_image(self):
        url1 = 'https://example.com/1.jpg'
        url2 = ''
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_relative_ok(self):
        url1 = 'https://example.com/1.jpg'
        url2 = '/some/path/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        result = image_check(html, self.allowed_hosts)
        self.assertTrue(result)

    def test_non_https(self):
        url1 = 'http://example.com/1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_missing_hostname(self):
        url1 = 'http:///1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_hostname_not_allowed1(self):
        url1 = 'https://xxx.example.com/1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_hostname_not_allowed2(self):
        url1 = 'https://xxx.example.com/1.jpg'
        url2 = 'https://yyy.example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_empty_string(self):
        result = image_check('')
        self.assertTrue(result)

    def test_whitespace(self):
        result = image_check('\r\n\r\n')
        self.assertTrue(result)
