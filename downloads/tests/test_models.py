"""Unit tests for downloads model helpers."""

import os

from django.test import SimpleTestCase

from downloads.models import download_path


class DownloadPathTestCase(SimpleTestCase):
    def test_returns_valid_path_without_raising(self):
        # download_path feeds a microsecond-derived value to hex(), which requires
        # an int. Python 3's true division (microsecond / 1000) makes it a float,
        # so hex() raises TypeError -- this guards against that regressing.
        path = download_path(None, 'track.mp3')

        self.assertIsInstance(path, str)
        parts = path.split(os.sep)
        # 'downloads' / year / month / day / <hex dir> / filename
        self.assertEqual(parts[0], 'downloads')
        self.assertEqual(parts[-1], 'track.mp3')
        self.assertTrue(parts[-2], 'the hex directory component should be non-empty')
