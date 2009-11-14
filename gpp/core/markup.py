"""
This is a thin wrapper around the Markdown class which deals with the
differences in Markdown versions on the production and development server.
This code was inspired by the code in 
django/contrib/markup/templatetags/markup.py.
Currently, we only have to worry about Markdown 1.6b and 2.0.
"""
import markdown as _markdown
from django.utils.encoding import force_unicode

from smiley.utils import smilify

class Markdown(object):

    def __init__(self, safe_mode='escape'):
        # Unicode support only in markdown v1.7 or above. Version_info
        # exists only in markdown v1.6.2rc-2 or above.
        self.unicode_support = getattr(_markdown, "version_info", None) >= (1, 7)
        self.md = _markdown.Markdown(safe_mode=safe_mode)

    def convert(self, s):
        if self.unicode_support:
            return self.md.convert(force_unicode(s))
        else:
            return force_unicode(self.md.convert(s))


def markdown(s):
    md = Markdown()
    return md.convert(s)
