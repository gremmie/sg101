"""
This module contains a class derived from Python's HTMLParser to convert HTML to
Markdown. Currently this class only supports those HTML tags that have counter-
parts in BBCode used by stock phpBB 2.x.

In other words, this class was created to help convert data from a phpBB
forum to Markdown syntax and its scope is currently limited to that task.

"""
from HTMLParser import HTMLParser
import htmlentitydefs


# Let's call Markdown markup entities "elements" to avoid confusion
# with HTML tags.

class ElementBase(object):
    """
    Base class for all Markdown elements.

    """
    def __init__(self, attrs=None):
        self.data = u''
        self.attrs = dict(attrs) if attrs else {}

    def add_data(self, data):
        self.data += data

    def markdown(self):
        return self.data


class TextElement(ElementBase):
    """
    TextElements represent text fragments not inside HTML tags.
    """
    pass


class EmphasisElement(ElementBase):
    """
    An EmphasisElement is a Markdown element used to indicate emphasis and is
    represented by placing characters around text. E.g. _em_, **bold**

    """
    def __init__(self, tag, attrs):
        super(EmphasisElement, self).__init__(attrs)
        self.tag = tag

    def markdown(self):
        return u'%s%s%s' % (self.tag, self.data, self.tag)


def create_emphasis(tag):
    """
    Returns a function that creates an EmphasisElement using the supplied
    tag.

    """
    def inner(attrs):
        return EmphasisElement(tag, attrs)
    return inner


class HtmlElement(ElementBase):
    """
    Markdown also accepts HTML markup. This element represents a HTML tag that
    maps to itself in Markdown.

    """
    def __init__(self, tag, attrs):
        super(HtmlElement, self).__init__(attrs)
        self.tag = tag

    def markdown(self):
        return u'<%s>%s</%s>' % (self.tag, self.data, self.tag)


def create_html(tag):
    """
    Returns a function that creates a HtmlElement using the supplied tag.

    """
    def inner(attrs):
        return HtmlElement(tag, attrs)
    return inner


class QuoteElement(ElementBase):
    """
    Class to represent a blockquote in Markdown.

    """
    def markdown(self):
        return u'> %s\n\n' % self.data.replace('\n', '\n> ')


class BreakElement(ElementBase):
    """
    Class to represent a linebreak in Markdown.

    """
    def markdown(self):
        return u'  \n'


class DivElement(ElementBase):
    """
    This class maps a HTML <div> into a block of text surrounded by newlines.

    """
    def markdown(self):
        return u'\n%s\n' % self.data


class LinkElement(ElementBase):
    """
    This class maps HTML <a> tags into Markdown links.
    If no data is present, the actual href is used for the link text.

    """
    def markdown(self):
        try:
            url = self.attrs['href']
        except KeyError:
            return self.data if self.data else u''

        text = self.data if self.data else url
        return u'[%s](%s)' % (text, url)


class ImageElement(ElementBase):
    """
    This class maps HTML <img> tags into Markdown.
    This element assumes no alt text is present, and simply uses the word
    'image' for the alt text.

    """
    def markdown(self):
        try:
            url = self.attrs['src']
        except KeyError:
            return u' (missing image) '
        return u'![image](%s)' % url


class CodeElement(ElementBase):
    """
    This class is used to create code blocks in Markdown.

    """
    def markdown(self):
        return u'    %s\n' % self.data.replace('\n', '\n    ')


# List (ordered & unordered) support:

class ListElement(ElementBase):
    """
    This class creates Markdown for unordered lists. The bullet() method can be
    overridden to create ordered lists.

    """
    def __init__(self, attrs=None):
        super(ListElement, self).__init__(attrs)
        self.items = []
        self.list_nesting = 1

    def add_data(self, data):
        self.items.append(data)

    def bullet(self):
        return u'*'

    def markdown(self):
        bullet_str = self.bullet()
        indent = u' ' * (4 * (self.list_nesting - 1))
        s = u''
        for item in self.items:
            s += u'\n%s%s %s' % (indent, bullet_str, item)
        return s


class OrderedListElement(ListElement):
    """
    This class creates Markdown for ordered lists.

    """
    def bullet(self):
        return '1.'


class ItemElement(ElementBase):
    """
    This element is used to represent ordered & unordered list items.

    """
    pass

###############################################################################
###############################################################################

class MarkdownWriter(HTMLParser):
    """
    This class is an HTMLParser that converts a subset of HTML to Markdown.

    """

    elem_factories = {
        'a': LinkElement,
        'blockquote': QuoteElement,
        'br': BreakElement,
        'div': DivElement,
        'em': create_emphasis('_'),
        'img': ImageElement,
        'li': ItemElement,
        'ol': OrderedListElement,
        'pre': CodeElement,
        's': create_html('strike'),
        'strong': create_emphasis('**'),
        'u': create_html('u'),
        'ul': ListElement,
    }

    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()

    def handle_starttag(self, tag, attrs):
        if tag in self.elem_factories:
            factory = self.elem_factories[tag]
            element = factory(attrs)
        else:
            element = TextElement()

        self._push_elem(element)

    def handle_endtag(self, tag):
        self._pop_elem()

    def handle_data(self, data):
        if len(self.elem_stack) == 0:
            self._push_elem(TextElement())
        self._add_data(data)

    def handle_entityref(self, name):
        try:
            text = unichr(htmlentitydefs.name2codepoint[name])
        except KeyError:
            text = name
        self.handle_data(text)

    def handle_charref(self, name):
        self.handle_data(unichr(int(name)))

    def reset(self):
        HTMLParser.reset(self)
        self.elem_stack = []
        self.elements = []
        self.list_nesting = 0

    def _push_elem(self, tag):
        if len(self.elem_stack) and isinstance(self.elem_stack[-1], TextElement):
            self._pop_elem()
        if isinstance(tag, ListElement):
            self.list_nesting += 1
            tag.list_nesting = self.list_nesting
        self.elem_stack.append(tag)

    def _pop_elem(self):
        try:
            element = self.elem_stack.pop()
        except IndexError:
            # pop from empty list => bad HTML input; ignore it
            return

        if isinstance(element, ListElement):
            self.list_nesting -= 1
        if len(self.elem_stack):
            self.elem_stack[-1].add_data(element.markdown())
        else:
            self.elements.append(element)

    def _add_data(self, data):
        self.elem_stack[-1].add_data(data)

    def markdown(self):
        while len(self.elem_stack):
            self._pop_elem()
        text_list = [e.markdown() for e in self.elements]
        return u''.join(text_list)
