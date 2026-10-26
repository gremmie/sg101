"""This module contains routines for downloading files."""

import ipaddress
import logging
import mimetypes
import os
import socket
import tempfile
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError
from urllib3.util import connection as urllib3_connection


logger = logging.getLogger(__name__)

ALLOWED_PORTS = {80, 443}
MAX_REDIRECTS = 5


class DownloadError(Exception):
    """The file could not be fetched."""


class NotAccepted(DownloadError):
    """The response was not of the content type asked for."""
    def __init__(self, content_type):
        super().__init__(content_type)
        self.content_type = content_type


class TooLarge(DownloadError):
    """The response was larger than the limit asked for."""


class Refused(DownloadError):
    """The URL, or a redirect from it, leads to an internal address or to a
    port other than 80 or 443. Nothing was sent to it."""


def is_allowed_address(address):
    """True if address is one the public internet routes to: not loopback,
    private, link-local, shared, reserved, multicast or unspecified."""
    ip = ipaddress.ip_address(address)
    # is_global is true of multicast, so that is excluded on its own.
    return ip.is_global and not ip.is_multicast


class _CheckedConnectionMixin:
    """Checks the port and every address a host name resolves to before the
    socket is opened, then connects to the address that was checked.

    Every connection passes through here, redirects included, and the name is
    looked up only once, so a name cannot pass the check with one address and
    then connect to another.
    """
    def _new_conn(self):
        if self.port not in ALLOWED_PORTS:
            raise Refused('port %s' % self.port)
        infos = socket.getaddrinfo(self._dns_host, self.port,
                                   type=socket.SOCK_STREAM)
        addresses = [info[4][0] for info in infos]
        for address in addresses:
            if not is_allowed_address(address):
                raise Refused('%s is %s' % (self.host, address))
        # Connect to the address itself, leaving self.host alone: it is the
        # name the Host header carries and TLS verifies the certificate for.
        # The error mapping is urllib3's own _new_conn's.
        try:
            sock = urllib3_connection.create_connection(
                (addresses[0], self.port), self.timeout,
                source_address=self.source_address,
                socket_options=self.socket_options)
        except TimeoutError as ex:
            raise ConnectTimeoutError(
                self, 'Connection to %s timed out' % self.host) from ex
        except OSError as ex:
            raise NewConnectionError(
                self, 'Failed to establish a new connection: %s' % ex) from ex
        return sock


class _CheckedHTTPConnection(_CheckedConnectionMixin, HTTPConnection):
    pass


class _CheckedHTTPSConnection(_CheckedConnectionMixin, HTTPSConnection):
    pass


class _CheckedHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = _CheckedHTTPConnection


class _CheckedHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _CheckedHTTPSConnection


class _CheckedAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        super().init_poolmanager(*args, **kwargs)
        self.poolmanager.pool_classes_by_scheme = {
            'http': _CheckedHTTPConnectionPool,
            'https': _CheckedHTTPSConnectionPool,
        }


_session = requests.Session()
# A proxy taken from the environment would make the connection, not us.
_session.trust_env = False
_session.max_redirects = MAX_REDIRECTS
_session.mount('http://', _CheckedAdapter())
_session.mount('https://', _CheckedAdapter())


def download_file(url, path=None, timeout=None, max_bytes=None, accept=None):
    """Downloads the file at the given source URL and stores it in the
    filename given by path. If path is None, a temporary file will be created.

    Returns the path to the downloaded file. Raises DownloadError if the file
    could not be fetched, Refused if it or a redirect leads to an internal
    address or another port, NotAccepted if accept is given and the response's
    content type does not start with it, and TooLarge if max_bytes is given and
    the response is larger. Nothing is left on disk when an exception is
    raised.
    """
    logger.info("download_file from %s; path=%s", url, path)

    try:
        r = _session.get(url, stream=True, timeout=timeout)
    except Refused as ex:
        logger.warning("download_file from %s: refused, %s", url, ex)
        raise
    except requests.RequestException as ex:
        logger.warning("download_file from %s: %s", url, ex)
        raise DownloadError(str(ex)) from ex

    try:
        if r.status_code != 200:
            logger.warning("download_file from %s: error code %d", url,
                           r.status_code)
            raise DownloadError('status %d' % r.status_code)

        content_type = r.headers.get('content-type', '').split(';')[0].strip()
        if accept and not content_type.startswith(accept):
            logger.info("download_file from %s: refused content type %r", url,
                        content_type)
            raise NotAccepted(content_type)

        declared = r.headers.get('content-length')
        if max_bytes and declared and declared.isdigit() and \
                int(declared) > max_bytes:
            raise TooLarge('%s bytes declared' % declared)

        if not path:
            suffix = mimetypes.guess_extension(content_type) if content_type else ''

            # mimetypes currently returns '.jpe' for jpeg; so fix that up here...
            if suffix == '.jpe':
                suffix = '.jpg'
            elif not suffix:
                # No content-type so guess based on extension if we can
                p = urlparse(url)
                suffix = os.path.splitext(p.path)[1]

            fd, path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)

        try:
            _save(r, path, max_bytes)
        except BaseException:
            os.remove(path)
            raise
    finally:
        r.close()

    file_size = os.stat(path).st_size
    logger.info("download_file retrieved %s bytes from %s; saved to %s", file_size, url, path)
    return path


def _save(response, path, max_bytes):
    """Write the response body to path, stopping once it passes max_bytes."""
    size = 0
    with open(path, 'wb') as fp:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            size += len(chunk)
            if max_bytes and size > max_bytes:
                raise TooLarge('more than %d bytes' % max_bytes)
            fp.write(chunk)


if __name__ == '__main__':
    import sys
    s = "%(asctime)s : %(levelname)s : %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=s)
    logging.info("argument is %s", sys.argv[1])
    result = download_file(sys.argv[1])
    if result:
        print(result)
