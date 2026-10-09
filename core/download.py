"""This module contains routines for downloading files."""

import logging
import mimetypes
import os
import tempfile
from urllib.parse import urlparse

import requests


logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """The file could not be fetched."""


class NotAccepted(DownloadError):
    """The response was not of the content type asked for."""
    def __init__(self, content_type):
        super().__init__(content_type)
        self.content_type = content_type


class TooLarge(DownloadError):
    """The response was larger than the limit asked for."""


def download_file(url, path=None, timeout=None, max_bytes=None, accept=None):
    """Downloads the file at the given source URL and stores it in the
    filename given by path. If path is None, a temporary file will be created.

    Returns the path to the downloaded file. Raises DownloadError if the file
    could not be fetched, NotAccepted if accept is given and the response's
    content type does not start with it, and TooLarge if max_bytes is given and
    the response is larger. Nothing is left on disk when an exception is
    raised.
    """
    logger.info("download_file from %s; path=%s", url, path)

    try:
        r = requests.get(url, stream=True, timeout=timeout)
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
