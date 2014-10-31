"""
Markup related utitlities useful for the entire project.

"""
import markdown as _markdown
from django.utils.encoding import force_unicode

from smiley import SmilifyMarkdown
from core.mdexts.urlize import UrlizeExtension
from core.mdexts.deleted import DelExtension
from core.html import clean_html


class Markdown(object):
    """
    This is a thin wrapper around the Markdown class.

    """
    def __init__(self):
        self.md = _markdown.Markdown(extensions=[
                                         UrlizeExtension(),
                                         'markdown.extensions.nl2br',
                                         DelExtension(),
                                     ])

    def convert(self, s):
        return clean_html(self.md.convert(force_unicode(s)))


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

    The relative_urls parameter controls whether the smileys are generated with
    relative or absolute URLs.

    """
    def __init__(self, relative_urls=True):
        self.md = Markdown()
        self.smiley = SmilifyMarkdown(relative_urls=relative_urls)

    def convert(self, s):
        return self.md.convert(self.smiley.convert(s))


def site_markup(s, relative_urls=True):
    """
    Convenience function for one-off site markup jobs.
    """
    sm = SiteMarkup(relative_urls=relative_urls)
    return sm.convert(s)
