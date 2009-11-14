"""
Smiley class and function.
"""
import re

from django.utils.safestring import SafeData
from django.utils.html import conditional_escape

from smiley.models import Smiley


class Smilify(object):
    """
    A class to "smilify" text by replacing text with HTML img tags of smilies.
    """
    def __init__(self):
        self.map = Smiley.objects.get_smiley_map()

    def convert(self, value, autoescape=False):
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
        

def smilify(value, autoescape=False):
    """
    A convenience function to "smilify" text by replacing text with HTML
    img tags of smilies.
    """
    s = Smilify()
    return s.convert(value, autoescape)

