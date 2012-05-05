"""
This module contains functions for working with data from the legacy phpBB
based website.
"""
import re
import htmlentitydefs


# BBCode tags used by the old site
BBCODE_TAGS = "b i u s url quote img list * code color size".split()

# Regular expressions used to get rid of phpBB's uid inside BBCode tags.
# This is a list of regular expression pairs. Element 0 of each pair
# is for the opening tag & element 1 is for the closing tag.

BBCODE_RES = [(
    re.compile(r"(\[%s):(?:[0-9a-fu]+:)?[0-9a-f]{10}" % tag),
    re.compile(r"(\[/%s):(?:[0-9a-fu]+:)?[0-9a-f]{10}\]" % tag)
) for tag in BBCODE_TAGS]


##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
# Source: http://effbot.org/zone/re-sub.htm#unescape-html
#
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def unphpbb(s, encoding='latin-1'):
    """Converts BBCode from phpBB database data into 'pure' BBCode.

    phpBB doesn't store plain BBCode in its database. The BBCode tags have
    "uids" added to them and the data has already been HTML entity'ized.
    This function removes the uid stuff and undoes the entity'ification and
    returns the result as a unicode string.

    If the input 's' is not already unicode, it will be decoded using the
    supplied encoding.

    """
    if not isinstance(s, unicode):
        s = s.decode(encoding, 'replace')
    for start, end in BBCODE_RES:
        s = re.sub(start, r'\1', s, re.MULTILINE)
        s = re.sub(end, r'\1]', s, re.MULTILINE)
    return unescape(s)
