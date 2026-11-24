"""
The V3 pagination fragment: Previous and Next as buttons at every width, an
icon and a word; on a phone, where the page numbers are hidden, icons alone,
with First and Last and the page the reader is on.

The icons are Foundation's media-player glyphs, whose names run the other way
from the buttons': fi-previous is skip-to-start, so First, and fi-next is
skip-to-end, so Last.

"""
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from core.paginator import DiggPaginator


def render_page(number, pages=28):
    paginator = DiggPaginator(range(pages * 10), 10, body=5, tail=2, margin=3, padding=2)
    return render_to_string('core/v3/pagination.html', {'page': paginator.page(number)})


ICON = '<i class="%s" aria-hidden="true"></i>'
BUTTONS = {
    # name: (icon, label, the word shown beside the icon on wider screens, phone only)
    'first': ('fi-previous', 'First page', None, True),
    'previous': ('fi-rewind', 'Previous page', 'Previous', False),
    'next': ('fi-fast-forward', 'Next page', 'Next', False),
    'last': ('fi-next', 'Last page', None, True),
}


def contents(name):
    icon, label, word, phone_only = BUTTONS[name]
    if word is None:
        return ICON % icon
    word = '<span class="show-for-medium">%s</span>' % word
    return ICON % icon + word if name == 'previous' else word + ICON % icon


def li_class(name):
    return 'pagination-button hide-for-medium' if BUTTONS[name][3] else 'pagination-button'


def link(name, page):
    label = BUTTONS[name][1]
    return ('<li class="%s"><a class="button small" href="./?page=%d" aria-label="%s">'
            '%s</a></li>' % (li_class(name), page, label, contents(name)))


def disabled(name):
    return ('<li class="%s"><span class="button small disabled" aria-hidden="true">'
            '%s</span></li>' % (li_class(name), contents(name)))


class V3PaginationTestCase(SimpleTestCase):

    def test_a_middle_page_links_every_way(self):
        html = render_page(3)
        self.assertInHTML(link('first', 1), html)
        self.assertInHTML(link('previous', 2), html)
        self.assertInHTML(link('next', 4), html)
        self.assertInHTML(link('last', 28), html)

    def test_a_phone_is_told_which_page_it_is_on(self):
        self.assertInHTML(
            '<li class="pagination-status hide-for-medium">3 of 28</li>', render_page(3))

    def test_the_page_numbers_stay_for_wider_screens(self):
        html = render_page(3)
        self.assertInHTML('<li><a href="./?page=27" aria-label="Page 27">27</a></li>', html)
        self.assertInHTML(
            '<li class="current"><span class="show-for-sr">You\'re on page</span> 3</li>', html)

    def test_the_first_page_greys_out_first_and_previous(self):
        html = render_page(1)
        self.assertInHTML(disabled('first'), html)
        self.assertInHTML(disabled('previous'), html)
        self.assertInHTML(link('next', 2), html)
        self.assertInHTML(link('last', 28), html)

    def test_the_last_page_greys_out_next_and_last(self):
        html = render_page(28)
        self.assertInHTML(link('first', 1), html)
        self.assertInHTML(link('previous', 27), html)
        self.assertInHTML(disabled('next'), html)
        self.assertInHTML(disabled('last'), html)
