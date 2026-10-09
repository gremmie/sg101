"""
Tests for core.download.download_file.

requests.get is replaced by a fake response; everything after it -- the temp
file, the size counting, the cleanup -- runs for real against a temporary
directory, because those are the parts that went wrong.
"""
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import requests

from core.download import DownloadError, NotAccepted, TooLarge, download_file


class FakeResponse:
    def __init__(self, status_code=200, content=b'', content_type='image/jpeg',
                 content_length=None):
        self.status_code = status_code
        self.content = content
        self.headers = {}
        if content_type:
            self.headers['content-type'] = content_type
        if content_length is not None:
            self.headers['content-length'] = str(content_length)
        self.closed = False
        self.read = False

    def iter_content(self, chunk_size=1):
        self.read = True
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start:start + chunk_size]

    def close(self):
        self.closed = True


class DownloadFileTestCase(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        # Temporary files the function makes for itself land here too, so a
        # test can see whether one was left behind.
        patcher = patch('core.download.tempfile.tempdir', self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def leftovers(self):
        return os.listdir(self.dir)

    def get(self, response):
        return patch('core.download.requests.get', return_value=response)

    def test_an_image_is_saved_and_its_path_returned(self):
        with self.get(FakeResponse(content=b'JPEGDATA')) as get:
            path = download_file('https://example.com/a.jpg', timeout=5,
                                 accept='image/')
        with open(path, 'rb') as fp:
            self.assertEqual(fp.read(), b'JPEGDATA')
        self.assertTrue(path.endswith('.jpg'))
        get.assert_called_once_with('https://example.com/a.jpg', stream=True,
                                    timeout=5)

    def test_a_given_path_is_used(self):
        target = os.path.join(self.dir, 'given.png')
        with self.get(FakeResponse(content=b'PNG', content_type='image/png')):
            self.assertEqual(download_file('https://example.com/x', target),
                             target)

    def test_no_content_type_takes_the_suffix_from_the_url(self):
        with self.get(FakeResponse(content=b'GIF', content_type=None)):
            path = download_file('https://example.com/pic.gif')
        self.assertTrue(path.endswith('.gif'))

    def test_a_non_200_raises(self):
        with self.get(FakeResponse(status_code=404)):
            with self.assertRaises(DownloadError):
                download_file('https://example.com/gone.jpg')
        self.assertEqual(self.leftovers(), [])

    def test_a_request_failure_raises_a_download_error(self):
        with patch('core.download.requests.get',
                   side_effect=requests.ConnectTimeout('slow')):
            with self.assertRaises(DownloadError):
                download_file('https://example.com/a.jpg', timeout=5)

    def test_a_web_page_is_refused_before_anything_is_saved(self):
        response = FakeResponse(content=b'<html>', content_type='text/html; charset=utf-8')
        with self.get(response):
            with self.assertRaises(NotAccepted) as raised:
                download_file('https://youtu.be/x', accept='image/')
        self.assertEqual(raised.exception.content_type, 'text/html')
        self.assertEqual(self.leftovers(), [])
        self.assertTrue(response.closed)

    def test_a_missing_content_type_is_refused_when_one_is_required(self):
        with self.get(FakeResponse(content=b'?', content_type=None)):
            with self.assertRaises(NotAccepted):
                download_file('https://example.com/a', accept='image/')

    def test_a_declared_size_over_the_cap_is_refused_before_reading(self):
        response = FakeResponse(content=b'x' * 100, content_length=100)
        with self.get(response):
            with self.assertRaises(TooLarge):
                download_file('https://example.com/big.jpg', max_bytes=10)
        self.assertEqual(self.leftovers(), [])
        self.assertFalse(response.read)

    def test_an_undeclared_size_over_the_cap_is_stopped_and_removed(self):
        response = FakeResponse(content=b'x' * 100)
        with self.get(response):
            with self.assertRaises(TooLarge):
                download_file('https://example.com/big.jpg', max_bytes=10)
        self.assertEqual(self.leftovers(), [])

    def test_a_size_at_the_cap_is_accepted(self):
        with self.get(FakeResponse(content=b'x' * 10)):
            path = download_file('https://example.com/a.jpg', max_bytes=10)
        self.assertEqual(os.path.getsize(path), 10)

    def test_a_not_accepted_and_a_too_large_are_both_download_errors(self):
        # One except clause in the caller covers every way a fetch can fail.
        self.assertTrue(issubclass(NotAccepted, DownloadError))
        self.assertTrue(issubclass(TooLarge, DownloadError))
