"""Testing our custom Markdown extensions."""

import unittest

import markdown

from core.mdexts.ssl_images import SslImagesExtension


class SslImagesExtTestCase(unittest.TestCase):
    """Tests for the SslImagesExtension."""

    def setUp(self):
        self.md = markdown.Markdown(extensions=[SslImagesExtension()])

    def test_simple(self):
        self.assertEqual(self.md.convert(''), '')
        self.assertEqual(self.md.convert('1'), '<p>1</p>')

    def test_no_change(self):
        self.assertEqual(self.md.convert('![image](https://example.com/1.jpg)'),
                         u'<p><img alt="image" src="https://example.com/1.jpg" /></p>')

    def test_change(self):
        text = u'![image](http://example.com/1.jpg)'
        html = u'<p><a href="http://example.com/1.jpg">Click for image</a></p>'
        self.assertEqual(self.md.convert(text), html)
