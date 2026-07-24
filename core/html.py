"""Common HTML related functions"""
from urllib.parse import urlparse

import bleach
from lxml import etree

from django.conf import settings


# Each entry in the _CLEAN_PROFILES dict is a profile name -> 3-tuple pair. The
# tuple consists of (allowed_tags_list, allowed_attributes_dict,
# allowed_styles_list)
#
_CLEAN_PROFILES = {
    'comments': (
        [
            'a', 'b', 'blockquote', 'br', 'code', 'del', 'em',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr',
            'i', 'img', 'li', 'ol', 'p', 'pre', 'strong', 'ul',
        ],
        {
            'a': ['href'],
            'img': ['src', 'alt', 'title'],
        },
        [],
    ),
    'news': (
        [
            'a', 'b', 'blockquote', 'br', 'caption', 'center', 'code', 'col',
            'colgroup', 'dd', 'del', 'div', 'dl', 'dt', 'em',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr',
            'i', 'img', 'ins', 'li', 'ol', 'p', 'pre', 'small', 'strike',
            'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
            'thead', 'tr', 'tt', 'u', 'ul',
        ],
        {
            'a': ['href'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        },
        [],
    ),
}


def clean_html(text, profile='comments'):
    """Cleans HTML of dangerous tags and content."""
    text = text.strip()
    if not text:
        return text

    tags, attrs, styles = _CLEAN_PROFILES[profile]

    return bleach.clean(text, tags=tags, attributes=attrs, styles=styles,
        strip=True, strip_comments=True)


class ImageCheckError(Exception):
    """Exception for the image_check() function"""


ALLOWED_HOSTS = set(settings.USER_IMAGES_SOURCES)


def image_check(html, allowed_hosts=None):
    """Returns true if all image tags in the given html come from hosts
    specified in the allowed_hosts container using https.

    An ImageCheckError is raised if the following problems are detected:
        * the image src is missing altogether
        * the scheme is missing or not https
        * the hostname is missing
        * the hostname is not in allowed_hosts

    If allowed_hosts is not None, it will be used as the whitelist of allowed
    hosts. If None, USER_IMAGES_SOURCES from settings will be used as the
    whitelist.
    """
    html = html.strip()
    if not html:
        return True

    if not allowed_hosts:
        allowed_hosts = ALLOWED_HOSTS

    root = etree.HTML(html)
    for img in root.iter('img'):
        src = img.get('src')
        if not src:
            raise ImageCheckError("Missing image source")
        r = urlparse(src)

        if not r.scheme and not r.hostname:
            # relative URL is ok
            continue
        if r.scheme != 'https':
            raise ImageCheckError("Image must be accessed via https")
        if not r.hostname:
            raise ImageCheckError("Missing image hostname")
        if r.hostname not in allowed_hosts:
            raise ImageCheckError("Invalid image source")

    return True
