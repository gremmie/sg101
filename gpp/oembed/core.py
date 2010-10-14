"""
This module contains core functionality for the oembed application.
"""
from __future__ import with_statement
import urllib
import urllib2
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import django.utils.simplejson as json


USER_AGENT = 'gremmies python oembed'


def get_oembed(api_endpoint, url, format='json', **opts):
    """
    Perform the GET request to retrieve the embedded media data from the given
    API endpoint for the given URL. Return the result as a Python dictionary.

    format specifies the response format, and should be 'json' or 'xml'.
    opts are any additional GET options that should be present in the GET
    request.

    """
    opts['url'] = url
    opts['format'] = format
    api_url = "%s?%s" % (api_endpoint, urllib.urlencode(opts))

    headers = {
        'User-Agent': USER_AGENT, 
        'Accept-Encoding': 'gzip',
    }
    request = urllib2.Request(api_url, headers=headers)

    opener = urllib2.build_opener()
    f = opener.open(request)
    headers = f.info()
    result = f.read()
    f.close()

    if headers.get('content-encoding') == 'gzip':
        with gzip.GzipFile(fileobj=StringIO(result)) as f:
            result = f.read()

    return json.loads(result)

if __name__ == "__main__":
    try:
        print get_oembed("http://www.youtube.com/oembed",
                #"http://www.youtube.com/watch?v=7_IMzJldOf4")
                "http://www.youtube.com/watch?v=99999999999")
    except urllib2.HTTPError, e:
        print e
