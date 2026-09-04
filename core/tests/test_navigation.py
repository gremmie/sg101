"""Tests that no page still links to the retired MoinMoin wiki.

`wiki.surfguitar101.com` outlives this branch: it keeps running on the old host
until that host is retired, so the links were live right up to the moment they
were removed here. What must not happen is the new site launching with menu
entries pointing at a hostname that is about to stop resolving.

These render real pages rather than grepping the templates, for the same reason
the calendar's navigation tests do -- a template is only a claim about what a
page contains until something renders it. The site runs two live designs and
both carried the link: the forums and flatpages wear `base.html`, everything
else wears `v3/base.html`.

The wiki's content is archived under `archive/wiki/`.

"""
from django.test import TestCase
from django.urls import reverse


class NoWikiLinksTestCase(TestCase):

    def _assert_no_wiki_link(self, url_name):
        response = self.client.get(reverse(url_name))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'wiki.surfguitar101.com')

    def test_the_forums_design_has_no_wiki_link(self):
        """`base.html`, which carried it in the main menu."""
        self._assert_no_wiki_link('forums-index')

    def test_the_v3_design_has_no_wiki_link(self):
        """`v3/base.html`, which carried it under Surf Music."""
        self._assert_no_wiki_link('home')

    def test_the_contact_page_does_not_send_people_to_the_faq(self):
        """The contact form pointed at `Sg101Faq`, and nothing replaces it.

        There is no other FAQ on the site, so the sentence went rather than
        being repointed at something that does not exist.
        """
        self._assert_no_wiki_link('contact-form')
