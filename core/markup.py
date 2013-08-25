"""
Markup related utitlities useful for the entire project.
"""
import markdown as _markdown
from django.utils.encoding import force_unicode

from smiley import SmilifyMarkdown

class Markdown(object):
    """
    This is a thin wrapper around the Markdown class which deals with the
    differences in Markdown versions on the production and development server.
    This code was inspired by the code in
    django/contrib/markup/templatetags/markup.py.
    Currently, we only have to worry about Markdown 1.6b and 2.0.
    """
    def __init__(self, safe_mode='escape'):
        self.md = _markdown.Markdown(safe_mode=safe_mode,
                                extensions=['urlize', 'nl2br', 'del'])

    def convert(self, s):
        return self.md.convert(force_unicode(s))


def markdown(s):
    """
    A convenience function for one-off markdown jobs.
    """
    md = Markdown()
    return md.convert(s)


class SiteMarkup(object):
    """
    This class provides site markup by combining markdown and
    our own smiley markup.
    """
    def __init__(self):
        self.md = Markdown()
        self.smiley = SmilifyMarkdown()

    def convert(self, s):
        return self.md.convert(self.smiley.convert(s))


def site_markup(s):
    """
    Convenience function for one-off site markup jobs.
    """
    sm = SiteMarkup()
    return sm.convert(s)
