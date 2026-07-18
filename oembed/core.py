"""
This module contains core functionality for the oembed application.

"""
from __future__ import print_function

from contextlib import closing
import json
import urllib
import urllib2
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO



USER_AGENT = 'gremmies python oembed'


def get_oembed(api_endpoint, url, fmt='json', **opts):
    """
    Perform the GET request to retrieve the embedded media data from the given
    API endpoint for the given URL. Return the result as a Python dictionary.

    fmt specifies the response format, and should be 'json' or 'xml'.
    opts are any additional GET options that should be present in the GET
    request.

    """
    opts['url'] = url
    opts['format'] = fmt
    api_url = "%s?%s" % (api_endpoint, urllib.urlencode(opts))

    headers = {
        'User-Agent': USER_AGENT,
        'Accept-Encoding': 'gzip',
    }
    request = urllib2.Request(api_url, headers=headers)
    with closing(urllib2.urlopen(request)) as response:
        headers = response.info()
        result = response.read()

    if headers.get('content-encoding') == 'gzip':
        with closing(gzip.GzipFile(fileobj=StringIO(result))) as f:
            result = f.read()

    return json.loads(result)

if __name__ == "__main__":
    try:
        print(get_oembed("http://www.youtube.com/oembed",
                         "http://www.youtube.com/watch?v=7_IMzJldOf4",
                         scheme='https'))
    except urllib2.HTTPError as e:
        print(e)
