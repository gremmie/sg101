"""
Tests for core.download.download_file.

The session's get is replaced by a fake response; everything after it -- the
temp file, the size counting, the cleanup -- runs for real against a temporary
directory, because those are the parts that went wrong.

The address checks below go through the real requests and urllib3 stack, with
the name lookup and the socket replaced, so nothing leaves the machine.
"""
import http.server
import logging
import os
import shutil
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

import requests
from urllib3.util import connection as urllib3_connection

from core.download import (MAX_REDIRECTS, DownloadError, NotAccepted, Refused,
                           TooLarge, _CheckedHTTPSConnection, download_file,
                           is_allowed_address)


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
        return patch('core.download._session.get', return_value=response)

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
        with patch('core.download._session.get',
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


def addrinfo(*addresses, port=80):
    """What socket.getaddrinfo returns for a name with these addresses."""
    result = []
    for address in addresses:
        family = socket.AF_INET6 if ':' in address else socket.AF_INET
        sockaddr = (address, port, 0, 0) if ':' in address else (address, port)
        result.append((family, socket.SOCK_STREAM, 6, '', sockaddr))
    return result


class AllowedAddressTestCase(unittest.TestCase):

    def test_internal_addresses_are_refused(self):
        for address in ['127.0.0.1', '10.1.2.3', '172.17.0.2', '192.168.1.1',
                        '169.254.169.254', '100.64.0.1', '0.0.0.0',
                        '224.0.0.1', '::1', 'fe80::1', '::ffff:127.0.0.1',
                        'fc00::1', 'ff0e::1']:
            with self.subTest(address=address):
                self.assertFalse(is_allowed_address(address))

    def test_public_addresses_are_allowed(self):
        for address in ['93.184.215.14', '104.16.0.1', '2606:4700::1111']:
            with self.subTest(address=address):
                self.assertTrue(is_allowed_address(address))


class RefusedTestCase(unittest.TestCase):
    """A refusal happens before any socket is opened."""

    def setUp(self):
        self.connects = []

        def fake_connect(address, *args, **kwargs):
            self.connects.append(address)
            raise OSError('no network in tests')

        patcher = patch.object(urllib3_connection, 'create_connection',
                               side_effect=fake_connect)
        patcher.start()
        self.addCleanup(patcher.stop)

    def resolve(self, *addresses):
        return patch('core.download.socket.getaddrinfo',
                     return_value=addrinfo(*addresses))

    def test_an_internal_literal_is_refused(self):
        with self.assertRaises(Refused):
            download_file('http://10.0.0.1/a.jpg')
        self.assertEqual(self.connects, [])

    def test_a_name_resolving_to_an_internal_address_is_refused(self):
        with self.resolve('172.18.0.5'):
            with self.assertRaises(Refused):
                download_file('http://redis/a.jpg')
        self.assertEqual(self.connects, [])

    def test_one_internal_address_among_public_ones_is_refused(self):
        with self.resolve('93.184.215.14', '127.0.0.1'):
            with self.assertRaises(Refused):
                download_file('https://example.com/a.jpg')
        self.assertEqual(self.connects, [])

    def test_another_port_is_refused_without_a_lookup(self):
        with self.resolve('93.184.215.14') as lookup:
            with self.assertRaises(Refused):
                download_file('http://example.com:8080/a.jpg')
        lookup.assert_not_called()
        self.assertEqual(self.connects, [])

    def test_a_public_name_connects_to_the_address_that_was_checked(self):
        # One lookup, and the socket goes to its answer: a second lookup is
        # how a rebinding name would swap in an internal address.
        with self.resolve('93.184.215.14') as lookup:
            with self.assertRaises(DownloadError) as raised:
                download_file('https://example.com/a.jpg')
        self.assertNotIsInstance(raised.exception, Refused)
        self.assertEqual(lookup.call_count, 1)
        self.assertEqual(self.connects, [('93.184.215.14', 443)])

    def test_pinning_leaves_the_host_name_for_tls_to_verify(self):
        connection = _CheckedHTTPSConnection('example.com', 443)
        with self.resolve('93.184.215.14'), \
                patch.object(urllib3_connection, 'create_connection'):
            connection._new_conn()
        self.assertEqual(connection.host, 'example.com')

    def test_a_name_that_does_not_resolve_is_an_ordinary_failure(self):
        with patch('core.download.socket.getaddrinfo',
                   side_effect=socket.gaierror(-2, 'Name or service not known')):
            with self.assertRaises(DownloadError) as raised:
                download_file('https://no-such-host.example/a.jpg')
        self.assertNotIsInstance(raised.exception, Refused)

    def test_a_proxy_in_the_environment_is_not_used(self):
        # A proxy would make the connection itself, past the check.
        proxies = {'HTTP_PROXY': 'http://10.0.0.9:3128',
                   'HTTPS_PROXY': 'http://10.0.0.9:3128'}
        with patch.dict(os.environ, proxies), self.resolve('93.184.215.14'):
            with self.assertRaises(DownloadError):
                download_file('http://example.com/a.jpg')
        self.assertEqual(self.connects, [('93.184.215.14', 80)])

    def test_a_refusal_is_a_download_error_and_is_logged(self):
        self.assertTrue(issubclass(Refused, DownloadError))
        # The test settings disable logging wholesale, so assertLogs sees
        # nothing without this. Same dance as contact/tests/test_views.py.
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)
        with self.assertLogs('core.download', level='WARNING') as logged:
            with self.assertRaises(Refused):
                download_file('http://10.0.0.1/a.jpg')
        self.assertTrue(any('10.0.0.1' in line for line in logged.output))


class RedirectHandler(http.server.BaseHTTPRequestHandler):
    hits = 0
    host_header = None

    def do_GET(self):
        type(self).hits += 1
        type(self).host_header = self.headers.get('Host')
        if self.path == '/loop':
            self.send_response(302)
            self.send_header('Location', '/loop')
            self.end_headers()
        elif self.path == '/a.jpg':
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', '4')
            self.end_headers()
            self.wfile.write(b'JPEG')
        else:
            self.send_response(302)
            self.send_header('Location', 'http://internal.test/a.jpg')
            self.end_headers()

    def log_message(self, *args):
        pass


class RedirectTestCase(unittest.TestCase):
    """A real server on loopback, standing in for a public host.

    The address check is relaxed for this one server, its address and port,
    and nothing else, so the redirect it sends is checked like any other hop.
    """

    def setUp(self):
        self.server = http.server.HTTPServer(('127.0.0.1', 0), RedirectHandler)
        self.port = self.server.server_address[1]
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

        names = {'public.test': '127.0.0.1', 'internal.test': '10.0.0.1'}

        def fake_lookup(host, port, *args, **kwargs):
            # urllib3 passes the checked address back through getaddrinfo;
            # a literal resolves to itself, with no query.
            return addrinfo(names.get(host, host), port=port)

        real_check = is_allowed_address
        for patcher in [
            patch('core.download.socket.getaddrinfo', side_effect=fake_lookup),
            patch('core.download.is_allowed_address',
                  side_effect=lambda a: a == '127.0.0.1' or real_check(a)),
            patch('core.download.ALLOWED_PORTS', {80, 443, self.port}),
        ]:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.connects = []
        real_connect = urllib3_connection.create_connection

        def recording_connect(address, *args, **kwargs):
            self.connects.append(address)
            return real_connect(address, *args, **kwargs)

        patcher = patch.object(urllib3_connection, 'create_connection',
                               side_effect=recording_connect)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_stand_in_serves_an_image_through_the_checked_connection(self):
        path = download_file('http://public.test:%d/a.jpg' % self.port)
        self.addCleanup(os.remove, path)
        with open(path, 'rb') as fp:
            self.assertEqual(fp.read(), b'JPEG')
        self.assertEqual(self.connects, [('127.0.0.1', self.port)])
        # A virtual host is chosen by name; so is the certificate TLS checks.
        self.assertEqual(RedirectHandler.host_header, 'public.test:%d' % self.port)

    def test_redirects_stop_after_the_hop_limit(self):
        RedirectHandler.hits = 0
        with self.assertRaises(DownloadError):
            download_file('http://public.test:%d/loop' % self.port)
        self.assertEqual(RedirectHandler.hits, MAX_REDIRECTS + 1)

    def test_a_redirect_to_an_internal_host_is_refused(self):
        with self.assertRaises(Refused):
            download_file('http://public.test:%d/redirect' % self.port)
        self.assertEqual(self.connects, [('127.0.0.1', self.port)])
