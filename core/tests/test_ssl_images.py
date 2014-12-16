"""Unit tests for the ssl_images management command."""

import unittest

from core.management.commands.ssl_images import process_post


class ProcessPostTestCase(unittest.TestCase):

    def test_empty_string(self):
        s = process_post('')
        self.assertEqual(s, '')
