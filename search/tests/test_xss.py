"""
What a result page does with markup that members typed.

The indexed text is a mix of sources: forums.Post.body and bio's profile_text
hold markdown as it was typed, news.Story holds HTML already rendered from it,
and the ygroup archive holds both. So a search document's title and summary can
contain anything a member could write, and a result page is a second place --
after the page the content lives on -- where it gets shown.

Two paths matter, and they are not the same. Titles render through the template
and so are autoescaped. Snippets cannot be: ts_headline marks the matched words
and the markup it inserts has to survive, so those are escaped in Python and
marked safe afterwards.

"""

import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from forums.models import Category
from forums.models import Forum
from forums.models import Post
from forums.models import Topic
from search.models import SearchDocument


# Written as a member would type them. The entity-encoded forms matter most:
# body_text() unescapes what it strips tags from, so `&lt;` -- which is how a
# typed angle bracket survives in rendered HTML -- becomes a live tag in the
# indexed summary even though the literal form was stripped.
PAYLOADS = [
    '<script>alert(1)</script>',
    '&lt;script&gt;alert(1)&lt;/script&gt;',
    '<img src=x onerror=alert(1)>',
    '&lt;img src=x onerror=alert(1)&gt;',
    '&lt;svg onload=alert(1)&gt;',
    '"><script>alert(1)</script>',
    '&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;',
    "javascript:alert(1)",
    # The sentinels ts_headline wraps matched words in, typed by hand.
    '[[[hl]]]<script>alert(1)</script>[[[/hl]]]',
    '&lt;a href=&quot;javascript:alert(1)&quot;&gt;click&lt;/a&gt;',
]

# Every tag a result row is allowed to contain. Asserting against this rather
# than against a list of bad substrings, because a payload that survives as
# *text* is harmless -- `onload=` rendered inside a link label does nothing --
# while the thing that would actually hurt is a tag nobody meant to emit. So
# the invariant is: the only markup here is markup this template wrote.
ALLOWED_TAGS = re.compile(r"""
      </?d[ltd]>                      # the result list and its rows
    | <dl\ class="search-results">
    | <a\ href="/[^"]*">|</a>         # a link, always site-relative
    | <span\ class="highlight">|</span>
    """, re.VERBOSE)


class ResultPageEscapingTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.url = reverse('search')
        self.client.login(username='kahuna', password='pw')

    def results_region(self, response):
        """
        The rendered result rows alone.

        Scoped deliberately: the page carries its own <script> block for the
        check-all buttons, so a whole-page assertion would always trip.

        """
        match = re.search(r'<dl class="search-results">.*?</dl>',
                          response.content.decode(), re.S)
        return match.group(0) if match else ''

    def search(self, query='reverb'):
        return self.client.get(self.url, {'q': query})

    def assert_no_live_markup(self, html, payload):
        """Asserts every tag in the results region is one the template wrote."""
        self.assertTrue(html, msg='no results rendered for %r' % payload)
        for tag in re.findall(r'<[^>]*>', html):
            self.assertRegex(tag, ALLOWED_TAGS,
                             msg='payload %r produced tag %r' % (payload, tag))

    def test_a_payload_in_a_title_is_escaped(self):
        for payload in PAYLOADS:
            with self.subTest(payload=payload):
                SearchDocument.objects.all().delete()
                Topic.objects.all().delete()
                topic = Topic.objects.create(
                        forum=self.forum, user=self.user,
                        name='reverb %s' % payload)
                SearchDocument.objects.index_object(topic)
                self.assert_no_live_markup(
                        self.results_region(self.search()), payload)

    def test_a_payload_in_a_snippet_is_escaped(self):
        for payload in PAYLOADS:
            with self.subTest(payload=payload):
                SearchDocument.objects.all().delete()
                Topic.objects.all().delete()
                topic = Topic.objects.create(forum=self.forum, user=self.user,
                                             name='Amp settings')
                post = Post.objects.create(
                        topic=topic, user=self.user,
                        body='Talking about reverb here. %s' % payload)
                SearchDocument.objects.index_object(post)
                self.assert_no_live_markup(
                        self.results_region(self.search()), payload)

    def test_typed_sentinels_forge_a_span_and_nothing_more(self):
        # A member who types the sentinel does get a highlight span they did
        # not earn. That is the whole of the exposure, and it is why the
        # sentinels are replaced with a fixed string: the tag name and its one
        # attribute are literals here, so neither is ever attacker-controlled.
        # Text that looks like an attribute lands outside the tag, inert.
        topic = Topic.objects.create(forum=self.forum, user=self.user,
                                     name='Amp settings')
        post = Post.objects.create(
                topic=topic, user=self.user,
                body='reverb [[[hl]]]x[[[/hl]]] and [[[hl]]] onerror=alert(1)')
        SearchDocument.objects.index_object(post)

        html = self.results_region(self.search())
        self.assert_no_live_markup(html, 'typed sentinels')
        # Inert: after the span's '>', so it is text content, not an attribute.
        self.assertIn('<span class="highlight"> onerror=alert(1)', html)

    def test_the_query_is_escaped_where_the_form_echoes_it_back(self):
        # Reflected rather than stored: whatever was searched for comes back
        # in the box's value attribute, so a payload closing that attribute
        # would need no stored content at all.
        for payload in PAYLOADS:
            with self.subTest(payload=payload):
                response = self.search(payload)
                html = response.content.decode()
                box = re.search(r'<input[^>]*type="search"[^>]*>', html)
                self.assertIsNotNone(box, msg='search box did not render')
                self.assertNotIn('<', box.group(0)[1:-1])

    def test_the_query_is_url_encoded_into_the_pagination_links(self):
        # The page links carry the query forward through encode_params, whose
        # output lands in an href without going through autoescaping.
        for n in range(25):
            topic = Topic.objects.create(forum=self.forum, user=self.user,
                                         name='reverb tank %d' % n)
            SearchDocument.objects.index_object(topic)

        response = self.search('reverb "><script>alert(1)</script>')
        html = response.content.decode()
        links = re.findall(r'<a href="\?([^"]*)"', html)
        self.assertTrue(links, msg='no pagination links rendered')
        for link in links:
            self.assertNotIn('<', link)
            self.assertNotIn('"', link)

    def test_a_result_link_only_ever_points_at_this_site(self):
        # Escaping does not help inside an href, so the url column matters
        # separately. Every document builds it from reverse(), which is why.
        topic = Topic.objects.create(forum=self.forum, user=self.user,
                                     name='reverb tank')
        SearchDocument.objects.index_object(topic)
        html = self.results_region(self.search())
        for href in re.findall(r'href="([^"]*)"', html):
            self.assertTrue(href.startswith('/'),
                            msg='%r is not a site-relative link' % href)
