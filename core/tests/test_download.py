import unittest
from urlparse import urlparse, ParseResult

from mock import call, patch, mock_open, Mock

from core.download import download_file


class DownloadFileTestCase(unittest.TestCase):
    """Unit tests for the download_file function."""

    @patch('core.download.requests')
    def test_get_throws_exception(self, requests_mock):
        requests_mock.get.side_effect = RuntimeError('ope')
        r = None
        try:
            r = download_file('url', path='path', timeout=5.0)
        except RuntimeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception {}'.format(e))

        self.assertIsNone(r)
        self.assertEqual(requests_mock.get.mock_calls, [
            call('url', stream=True, timeout=5.0),
        ])

    @patch('core.download.requests')
    def test_get_returns_non_success(self, requests_mock):
        response_mock = Mock()
        response_mock.status_code = 404
        requests_mock.get.return_value = response_mock
        r = download_file('url', path='path', timeout=5.0)

        self.assertIsNone(r)
        self.assertEqual(requests_mock.get.mock_calls, [
            call('url', stream=True, timeout=5.0),
        ])

    @patch('core.download.os.stat')
    @patch('core.download.shutil.copyfileobj')
    @patch('core.download.requests')
    def test_happy_path_with_path_argument(self, requests_mock, copy_mock,
                                           stat_mock):
        response_mock = Mock()
        response_mock.status_code = 200
        requests_mock.get.return_value = response_mock

        stat_mock.st_size = 512

        open_mock = mock_open()
        with patch('__builtin__.open', open_mock):
            r = download_file('url', path='path', timeout=5.0)

        self.assertEqual(r, 'path')
        self.assertEqual(requests_mock.get.mock_calls, [
            call('url', stream=True, timeout=5.0),
        ])
        self.assertTrue(response_mock.raw.decode_content)
        self.assertEqual(copy_mock.mock_calls, [
            call(response_mock.raw, open_mock.return_value),
        ])

    @patch('core.download.os.remove')
    @patch('core.download.shutil.copyfileobj')
    @patch('core.download.requests')
    def test_copyfileobj_raises(self, requests_mock, copy_mock, remove_mock):
        response_mock = Mock()
        response_mock.status_code = 200
        requests_mock.get.return_value = response_mock

        copy_mock.side_effect = IOError

        open_mock = mock_open()
        with patch('__builtin__.open', open_mock):
            try:
                download_file('url', path='path', timeout=5.0)
            except IOError:
                pass
            else:
                self.fail('Should have thrown')

        self.assertEqual(requests_mock.get.mock_calls, [
            call('url', stream=True, timeout=5.0),
        ])
        self.assertTrue(response_mock.raw.decode_content)
        self.assertEqual(copy_mock.mock_calls, [
            call(response_mock.raw, open_mock.return_value),
        ])
        self.assertEqual(remove_mock.mock_calls, [
            call('path'),
        ])


    @patch('core.download.os')
    @patch('core.download.tempfile')
    @patch('core.download.mimetypes')
    @patch('core.download.os.remove')
    @patch('core.download.shutil.copyfileobj')
    @patch('core.download.requests')
    def test_happy_path_with_suffix(self, requests_mock, copy_mock, remove_mock,
                                    mime_mock, tempfile_mock, os_mock):
        response_mock = Mock()
        response_mock.status_code = 200
        requests_mock.get.return_value = response_mock

        response_mock.headers.get.return_value = 'image/jpeg'
        mime_mock.guess_extension.return_value = '.jpe'
        fd_mock = Mock()
        tempfile_mock.mkstemp.return_value = (fd_mock, 'temp-path')

        open_mock = mock_open()
        with patch('__builtin__.open', open_mock):
            download_file('url', timeout=5.0)

        self.assertEqual(requests_mock.get.mock_calls, [
            call('url', stream=True, timeout=5.0),
            call().headers.get('content-type'),
        ])
        self.assertEqual(response_mock.headers.get.mock_calls, [
            call('content-type'),
        ])
        self.assertEqual(mime_mock.guess_extension.mock_calls, [
            call('image/jpeg'),
        ])
        self.assertEqual(tempfile_mock.mkstemp.mock_calls, [
            call(suffix='.jpg'),
        ])
        self.assertEqual(os_mock.close.mock_calls, [
            call(fd_mock),
        ])
        self.assertTrue(response_mock.raw.decode_content)
        self.assertEqual(copy_mock.mock_calls, [
            call(response_mock.raw, open_mock.return_value),
        ])


    @patch('core.download.urlparse')
    @patch('core.download.os')
    @patch('core.download.tempfile')
    @patch('core.download.mimetypes')
    @patch('core.download.os.remove')
    @patch('core.download.shutil.copyfileobj')
    @patch('core.download.requests')
    def test_happy_path_with_no_suffix(self, requests_mock, copy_mock,
                                       remove_mock, mime_mock, tempfile_mock,
                                       os_mock, urlparse_mock):
        response_mock = Mock()
        response_mock.status_code = 200
        requests_mock.get.return_value = response_mock

        response_mock.headers.get.return_value = None
        urlparse_mock.return_value = ParseResult(
                scheme='https', netloc='www.example.com', path='/something.txt',
                params='', query='', fragment='')
        os_mock.path.splitext.return_value = ('/something', '.txt')
        fd_mock = Mock()
        tempfile_mock.mkstemp.return_value = (fd_mock, 'temp-path')

        open_mock = mock_open()
        with patch('__builtin__.open', open_mock):
            download_file('url', timeout=5.0)

        self.assertEqual(requests_mock.get.mock_calls, [
            call('url', stream=True, timeout=5.0),
            call().headers.get('content-type'),
        ])
        self.assertEqual(response_mock.headers.get.mock_calls, [
            call('content-type'),
        ])
        self.assertEqual(urlparse_mock.mock_calls, [
            call('url'),
        ])
        self.assertEqual(mime_mock.guess_extension.mock_calls, [])
        self.assertEqual(os_mock.path.splitext.mock_calls, [
            call('/something.txt'),
        ])
        self.assertEqual(tempfile_mock.mkstemp.mock_calls, [
            call(suffix='.txt'),
        ])
        self.assertEqual(os_mock.close.mock_calls, [
            call(fd_mock),
        ])
        self.assertTrue(response_mock.raw.decode_content)
        self.assertEqual(copy_mock.mock_calls, [
            call(response_mock.raw, open_mock.return_value),
        ])
