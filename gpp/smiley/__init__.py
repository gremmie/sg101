"""
Smiley class and function.
"""
import re

from django.utils.safestring import SafeData
from django.utils.html import conditional_escape

from smiley.models import Smiley


class Smilify(object):
    """
    A class to "smilify" text by replacing text with either HTML img tags 
    or markdown syntax for smiley images.
    """
    HTML = 0
    MARKDOWN = 1

    def __init__(self):
        self.map = Smiley.objects.get_smiley_map()

    def _convert(self, value, rep_index, autoescape=False):
        """
        Converts and returns the supplied text with either the
        HTML or markdown version of the smileys according to the
        output parameter.
        """
        if not autoescape or isinstance(value, SafeData):
            esc = lambda x: x
        else:
            esc = conditional_escape

        words = value.split()
        for i, word in enumerate(words):
            if word in self.map:
                words[i] = self.map[word][rep_index]
            else:
                words[i] = esc(words[i])
        return u' '.join(words)

    def html(self, value, autoescape=False):
        """
        Converts the supplied text by replacing the smiley codes with
        HTML img tags.
        """
        return self._convert(value, self.HTML, autoescape=autoescape)

    def markdown(self, value, autoescape=False):
        """
        Converts the supplied text by replacing the smiley codes with
        markdown image syntax.
        """
        return self._convert(value, self.MARKDOWN, autoescape=autoescape)
        

def smilify_html(value, autoescape=False):
    """
    A convenience function to "smilify" text by replacing text with HTML
    img tags of smilies.
    """
    s = Smilify()
    return s.html(value, autoescape=autoescape)


def smilify_markdown(value, autoescape=False):
    """
    A convenience function to "smilify" text by replacing text with 
    markdown syntax for the images of smilies.
    """
    s = Smilify()
    return s.markdown(value, autoescape=autoescape)
