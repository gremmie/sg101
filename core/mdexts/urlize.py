"""
This is a Python Markdown extension to automatically urlize text.
Originally found here:

https://github.com/r0wb0t/markdown-urlize

Modified by Brian Neal to update doctest for Python Markdown 2.5.x (extension
parameter changes).

Copyright (c) 2014 Rowan Nairn
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

A more liberal autolinker

Inspired by Django's urlize function.

Positive examples:

>>> import markdown
>>> md = markdown.Markdown(extensions=[UrlizeExtension()])

>>> md.convert('http://example.com/')
'<p><a href="http://example.com/">http://example.com/</a></p>'

>>> md.reset().convert('go to http://example.com')
'<p>go to <a href="http://example.com">http://example.com</a></p>'

>>> md.reset().convert('example.com')
'<p><a href="http://example.com">example.com</a></p>'

>>> md.reset().convert('example.net')
'<p><a href="http://example.net">example.net</a></p>'

>>> md.reset().convert('www.example.us')
'<p><a href="http://www.example.us">www.example.us</a></p>'

>>> md.reset().convert('(www.example.us/path/?name=val)')
'<p>(<a href="http://www.example.us/path/?name=val">www.example.us/path/?name=val</a>)</p>'

>>> md.reset().convert('go to <http://example.com> now!')
'<p>go to <a href="http://example.com">http://example.com</a> now!</p>'

Negative examples:

>>> md.reset().convert('del.icio.us')
'<p>del.icio.us</p>'

"""
import xml.etree.ElementTree as etree

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.util import AtomicString

# Global Vars
URLIZE_RE = '(%s)' % '|'.join([
    r'<(?:f|ht)tps?://[^>]*>',
    r'\b(?:f|ht)tps?://[^)<>\s]+[^.,)<>\s]',
    r'\bwww\.[^)<>\s]+[^.,)<>\s]',
    r'[^(<\s]+\.(?:com|net|org)\b',
])

# The priority Markdown gives its own `autolink`, which this replaces. Keeping
# the number means the pattern runs exactly where the built-in did: after the
# link and image patterns, so `[text](url)` and `![alt](url)` still win, and
# before `automail`.
AUTOLINK_PRIORITY = 120


class UrlizeInlineProcessor(InlineProcessor):
    """ Return a link Element given an autolink (`http://example/com`). """
    def handleMatch(self, m, data):
        url = m.group(1)

        if url.startswith('<'):
            url = url[1:-1]

        text = url

        if not url.split('://')[0] in ('http','https','ftp'):
            if '@' in url and not '/' in url:
                url = 'mailto:' + url
            else:
                url = 'http://' + url

        el = etree.Element("a")
        el.set('href', url)
        el.text = AtomicString(text)
        return el, m.start(0), m.end(0)

class UrlizeExtension(Extension):
    """ Urlize Extension for Python-Markdown. """

    def extendMarkdown(self, md):
        """ Replace autolink with UrlizeInlineProcessor """
        md.inlinePatterns.register(UrlizeInlineProcessor(URLIZE_RE, md),
                                   'autolink', AUTOLINK_PRIORITY)

def makeExtension(**kwargs):
    return UrlizeExtension(**kwargs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
