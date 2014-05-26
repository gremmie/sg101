"""
Smiley classes and functions.

"""
from django.utils.safestring import SafeData
from django.utils.html import conditional_escape

from smiley.models import Smiley


class SmilifyHtml(object):
    """
    A class to "smilify" text by replacing text with HTML img tags for smiley
    images.
    """
    def __init__(self):
        self.map = Smiley.objects.get_smiley_map()

    def convert(self, value, autoescape=False):
        """
        Converts and returns the supplied text with the HTML version of the
        smileys.
        """
        if not value:
            return u''

        if not autoescape or isinstance(value, SafeData):
            esc = lambda x: x
        else:
            esc = conditional_escape

        words = value.split()
        for i, word in enumerate(words):
            if word in self.map:
                words[i] = self.map[word]
            else:
                words[i] = esc(words[i])
        return u' '.join(words)


class SmilifyMarkdown(object):
    """
    A class to "smilify" text by replacing text with Markdown image syntax for
    smiley images.
    """
    def __init__(self, relative_urls=True):
        self.regexes = Smiley.objects.get_smiley_regexes(
                                        relative_urls=relative_urls)

    def convert(self, s):
        """
        Returns a string copy of the input s that has the smiley codes replaced
        with Markdown for smiley images.
        """
        if not s:
            return u''

        for regex, repl in self.regexes:
            s = regex.sub(repl, s)
        return s


def smilify_html(value, autoescape=False):
    """
    A convenience function to "smilify" text by replacing text with HTML
    img tags of smilies.
    """
    s = SmilifyHtml()
    return s.convert(value, autoescape=autoescape)

