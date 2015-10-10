"""This module contains routines for downloading files."""

import logging
import mimetypes
import os
import shutil
import tempfile

import requests


logger = logging.getLogger(__name__)


def download_file(url, path=None):
    """Downloads the image file from the given source URL and stores it in the
    filename given by path. If path is None, a temporary file will be created.

    If successful returns the path to the downloaded file. Otherwise None is
    returned.

    This function may raise various exceptions from the requests library.
    """
    logger.info("download_file from %s; path=%s", url, path)

    try:
        r = requests.get(url, stream=True)
    except requests.RequestException:
        logger.exception("download_file requests.get('%s') exception", url)
        raise

    if r.status_code != 200:
        logger.error("download_file from %s: error code %d", url, r.status_code)
        return None

    # Save file data

    if not path:
        content_type = r.headers.get('content-type')
        suffix = mimetypes.guess_extension(content_type) if content_type else ''
        if suffix == '.jpe':
            suffix = '.jpg'
        elif suffix is None:
            suffix = ''
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

    try:
        with open(path, 'wb') as fp:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, fp)
    except requests.RequestException:
        logger.exception("download_file download exception")
        os.remove(path)
        raise

    file_size = os.stat(path).st_size
    logger.info("download_file retrieved %s bytes from %s; saved to %s", file_size, url, path)
    return path


if __name__ == '__main__':
    import sys
    s = "%(asctime)s : %(levelname)s : %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=s)
    logging.info("argument is %s", sys.argv[1])
    result = download_file(sys.argv[1])
    if result:
        print result
