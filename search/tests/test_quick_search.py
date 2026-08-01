"""
Tests for the forums' duplicate-topic quick search.

The fragment behind `/search/topics/`, which the new-topic form requests when a
member clicks "Quick Search" beside the title field.

"""

import logging
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from forums.models import Category
from forums.models import Forum
from forums.models import Post
from forums.models import Topic
from news.models import Category as NewsCategory
from news.models import Story
from search.models import SearchDocument


class QuickSearchTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.url = reverse('search_topics')

    def login(self):
        self.assertTrue(self.client.login(username='kahuna', password='pw'))

    def index_topic(self, name):
        topic = Topic.objects.create(forum=self.forum, user=self.user,
                                     name=name)
        return SearchDocument.objects.index_object(topic)

    def check(self, title, **extra):
        """Requests the fragment the way forums.js does: a title, nothing else."""
        params = {'q': title}
        params.update(extra)
        return self.client.get(self.url, params)

    # -- the contract with forums.js -----------------------------------

    def test_the_path_the_javascript_hardcodes_still_resolves(self):
        # forums/static/js/forums.js requests this literally rather than
        # reversing the route name, so the path is part of the contract.
        self.assertEqual(self.url, '/search/topics/')

    def test_a_matching_topic_is_found(self):
        self.index_topic('Best reverb tank for a Jaguar')
        self.login()
        response = self.check('reverb tank')
        self.assertContains(response, 'Best reverb tank for a Jaguar')
        self.assertContains(response, Topic.objects.get().get_absolute_url())

    def test_no_matches_says_so_and_echoes_the_title(self):
        self.login()
        response = self.check('nothingmatchesthis')
        self.assertContains(response, 'No results found')
        self.assertContains(response, 'nothingmatchesthis')

    def test_only_topics_are_searched(self):
        # A post, a story and a profile all matching, none of which should
        # appear -- this checks for duplicate *topics*, not for content.
        self.index_topic('Amp settings')
        topic = Topic.objects.get(name='Amp settings')
        SearchDocument.objects.index_object(Post.objects.create(
                topic=topic, user=self.user, body='All about tremolo here.'))
        SearchDocument.objects.index_object(Story.objects.create(
                title='Tremolo news', submitter=self.user,
                category=NewsCategory.objects.create(title='News', slug='news'),
                short_text='', long_text=''))
        self.index_topic('Tremolo shootout')
        self.login()

        response = self.check('tremolo')
        self.assertContains(response, 'Tremolo shootout')
        self.assertNotContains(response, 'Tremolo news')
        self.assertNotContains(response, 'All about tremolo')

    def test_the_type_restriction_is_not_taken_from_the_request(self):
        # forums.js no longer sends `models` at all, and this is why it does not
        # need to: a caller asking for something else still gets topics.
        self.index_topic('Tremolo shootout')
        SearchDocument.objects.index_object(Story.objects.create(
                title='Tremolo news', submitter=self.user,
                category=NewsCategory.objects.create(title='News', slug='news'),
                short_text='', long_text=''))
        self.login()

        response = self.check('tremolo', models='news.story')
        self.assertContains(response, 'Tremolo shootout')
        self.assertNotContains(response, 'Tremolo news')

    # -- the markup bug this task fixes --------------------------------

    def assert_tags_balanced(self, response, tag):
        html = response.content.decode()
        self.assertEqual(len(re.findall(r'<%s[ >]' % tag, html)),
                         len(re.findall(r'</%s>' % tag, html)),
                         msg='<%s> is not balanced in:\n%s' % (tag, html))

    def test_the_results_branch_closes_its_tags(self):
        # The pre-existing bug: </fieldset> and </div> sat inside the {% else %}
        # branch, so neither closed when there *were* results -- exactly the
        # case a member sees when the feature is working.
        self.index_topic('Best reverb tank for a Jaguar')
        self.login()
        response = self.check('reverb tank')
        self.assertContains(response, 'Best reverb tank for a Jaguar')
        self.assert_tags_balanced(response, 'fieldset')
        self.assert_tags_balanced(response, 'div')

    def test_the_no_results_branch_closes_its_tags(self):
        self.login()
        response = self.check('nothingmatchesthis')
        self.assert_tags_balanced(response, 'fieldset')
        self.assert_tags_balanced(response, 'div')

    # -- edges ---------------------------------------------------------

    def test_anonymous_access_is_refused(self):
        self.index_topic('Best reverb tank for a Jaguar')
        response = self.check('reverb tank')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_an_empty_title_runs_no_query_and_does_not_error(self):
        # The JS declines to send an empty title, but the endpoint is reachable
        # directly, so it cannot rely on that.
        self.index_topic('Best reverb tank for a Jaguar')
        self.login()
        for title in ['', '   ']:
            with self.subTest(title=title):
                response = self.check(title)
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.context['page'])
                self.assertContains(response, 'No results found')

    def test_a_missing_query_parameter_is_harmless(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_malformed_input_does_not_error(self):
        self.login()
        for title in ['")(  AND', '"unclosed', '-only -exclusions']:
            with self.subTest(title=title):
                self.assertEqual(self.check(title).status_code, 200)

    # -- query logging -------------------------------------------------

    def enable_logging(self):
        """Undoes the suite-wide logging.disable() for one test."""
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, logging.CRITICAL)

    def test_a_check_is_logged_and_marked_as_a_quick_search(self):
        # It goes to search.log like a real search, but distinguishably: it
        # records what a member was about to post, not what they went looking
        # for, and reading the log for one should not be muddied by the other.
        self.login()
        self.enable_logging()
        with self.assertLogs('search', level='INFO') as captured:
            self.check('reverb tank')
        self.assertEqual(len(captured.records), 1)
        message = captured.records[0].getMessage()
        self.assertTrue(message.startswith('Forum topics quick search:'),
                        msg=message)
        self.assertIn('reverb tank', message)
        self.assertIn('kahuna', message)

    def test_an_empty_title_is_not_logged(self):
        self.login()
        self.enable_logging()
        with self.assertLogs('search', level='INFO') as captured:
            logging.getLogger('search').info('marker')
            self.check('')
        self.assertEqual([r.getMessage() for r in captured.records], ['marker'])

    def test_the_fragment_carries_no_page_chrome(self):
        # It is injected into the new-topic form, not rendered as a page.
        self.index_topic('Best reverb tank for a Jaguar')
        self.login()
        response = self.check('reverb tank')
        self.assertNotContains(response, '<html')
        self.assertNotContains(response, '<body')

    def test_more_results_than_fit_link_to_the_search_page(self):
        for n in range(25):
            self.index_topic('Reverb tank rebuild %d' % n)
        self.login()
        response = self.check('reverb tank')
        self.assertContains(response, 'First page of results shown')
        self.assertContains(response, reverse('search'))

    def test_nothing_renders_as_raw_template_syntax(self):
        # Django's {# #} is single-line only: a multi-line one is not a comment
        # at all and renders verbatim, which is how a comment reached the page.
        # Enough topics to spill past one page, because the block this guards
        # only renders when there is more than one -- a single topic exercises
        # neither the overflow paragraph nor anything inside it.
        for n in range(25):
            self.index_topic('Reverb tank rebuild %d' % n)
        self.login()
        for title in ['reverb tank', 'nothingmatchesthis']:
            with self.subTest(title=title):
                html = self.check(title).content.decode()
                for token in ['{#', '#}', '{%', '%}', '{{', '}}']:
                    self.assertNotIn(token, html)

    def test_the_overflow_link_keeps_the_search_page_on_topics(self):
        # The trap in dropping `models` from forums.js: this link used to
        # forward it from the request, so with nothing to forward the full
        # search page would have opened across all eight types.
        for n in range(25):
            self.index_topic('Reverb tank rebuild %d' % n)
        self.login()
        html = self.check('reverb tank').content.decode()
        link = re.search(r'<a href="([^"]*)">search page</a>', html)
        self.assertIsNotNone(link, msg=html)
        self.assertIn('models=forums.topic', link.group(1))
        self.assertIn('q=reverb', link.group(1))
