"""Tests for the search page."""

import logging
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from forums.models import Category
from forums.models import Forum
from forums.models import Topic
from search.models import SearchDocument


class SearchViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.url = reverse('search')

    def login(self):
        self.assertTrue(self.client.login(username='kahuna', password='pw'))

    def index_topic(self, name):
        topic = Topic.objects.create(forum=self.forum, user=self.user,
                                     name=name)
        return SearchDocument.objects.index_object(topic)

    def result_titles(self, response):
        return [row.title for row in response.context['page'].object_list]

    # -- the login gate ------------------------------------------------

    def test_the_landing_page_redirects_an_anonymous_visitor(self):
        response = self.client.get(self.url)
        self.assertRedirects(response,
                             '/accounts/login/?next=%s' % self.url)

    def test_a_query_from_an_anonymous_visitor_never_runs(self):
        self.index_topic('Reverb tank rebuild')
        response = self.client.get(self.url, {'q': 'reverb'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])
        self.assertIsNone(response.context)

    # -- the landing state ---------------------------------------------

    def test_the_landing_page_shows_the_form_and_the_tips(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['page'])
        self.assertContains(response, 'Search Tips')

    def test_the_landing_page_reports_no_errors(self):
        self.login()
        response = self.client.get(self.url)
        self.assertFalse(response.context['form'].is_bound)

    def test_the_landing_page_leaves_every_box_unchecked(self):
        self.login()
        response = self.client.get(self.url)
        boxes = re.findall(r'<input[^>]*type="checkbox"[^>]*>',
                           response.content.decode())
        self.assertEqual(len(boxes), 8)
        self.assertFalse([box for box in boxes if 'checked' in box])

    def test_the_tips_teach_the_websearch_syntax(self):
        self.login()
        response = self.client.get(self.url)
        self.assertContains(response, '"surf music"')
        self.assertContains(response, 'reverb -fender')

    def test_the_tips_no_longer_explain_the_three_boxes(self):
        self.login()
        response = self.client.get(self.url)
        self.assertNotContains(response, 'AND-ed together')

    # -- searching -----------------------------------------------------

    def test_a_search_returns_its_matches(self):
        self.index_topic('Reverb tank rebuild')
        self.index_topic('Jazzmaster setup')
        self.login()
        response = self.client.get(self.url, {'q': 'reverb'})
        self.assertEqual(self.result_titles(response), ['Reverb tank rebuild'])

    def test_a_search_reports_a_hit_count(self):
        self.index_topic('Reverb tank rebuild')
        self.login()
        response = self.client.get(self.url, {'q': 'reverb'})
        self.assertEqual(response.context['page'].paginator.count, 1)
        self.assertContains(response, '1 hit')

    def test_a_search_with_no_matches_says_so(self):
        self.login()
        response = self.client.get(self.url, {'q': 'nothingmatchesthis'})
        self.assertContains(response, 'No search results found')

    def test_only_the_checked_types_are_searched(self):
        self.index_topic('Reverb tank rebuild')
        self.login()
        response = self.client.get(self.url,
                                   {'q': 'reverb', 'models': ['news.story']})
        self.assertEqual(self.result_titles(response), [])

    def test_a_result_row_links_to_the_source_and_names_its_type(self):
        self.index_topic('Reverb tank rebuild')
        self.login()
        response = self.client.get(self.url, {'q': 'reverb'})
        self.assertContains(response, 'Forum Topic:')
        self.assertContains(response, Topic.objects.get().get_absolute_url())

    def test_an_empty_query_is_rejected_and_runs_nothing(self):
        self.index_topic('Reverb tank rebuild')
        self.login()
        response = self.client.get(self.url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['page'])
        self.assertContains(response, 'Please supply some search terms')

    def test_malformed_input_renders_results_rather_than_an_error(self):
        self.login()
        response = self.client.get(self.url, {'q': '")(  AND'})
        self.assertEqual(response.status_code, 200)

    # -- pagination ----------------------------------------------------

    def test_results_paginate(self):
        for n in range(25):
            self.index_topic('Reverb tank rebuild %d' % n)
        self.login()
        response = self.client.get(self.url, {'q': 'reverb'})
        page = response.context['page']
        self.assertEqual(page.paginator.count, 25)
        self.assertEqual(len(page.object_list), 20)
        self.assertTrue(page.has_next())

    def test_a_later_page_returns_the_rest(self):
        for n in range(25):
            self.index_topic('Reverb tank rebuild %d' % n)
        self.login()
        response = self.client.get(self.url, {'q': 'reverb', 'page': 2})
        self.assertEqual(len(response.context['page'].object_list), 5)

    def test_a_page_past_the_end_is_a_404(self):
        self.index_topic('Reverb tank rebuild')
        self.login()
        response = self.client.get(self.url, {'q': 'reverb', 'page': 99})
        self.assertEqual(response.status_code, 404)

    # -- query logging -------------------------------------------------

    def enable_logging(self):
        """
        Undoes the suite-wide logging.disable() for one test.

        sg101.settings.test disables logging outright to speed the suite up,
        and that beats assertLogs -- records never reach its handler.

        """
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, logging.CRITICAL)

    def test_an_executed_search_is_logged(self):
        self.login()
        self.enable_logging()
        with self.assertLogs('search', level='INFO') as captured:
            self.client.get(self.url, {'q': 'reverb',
                                       'models': ['news.story']})
        self.assertEqual(len(captured.records), 1)
        message = captured.records[0].getMessage()
        self.assertIn('reverb', message)
        self.assertIn('news.story', message)
        self.assertIn('kahuna', message)

    def test_a_rejected_query_is_not_logged(self):
        self.login()
        self.enable_logging()
        with self.assertLogs('search', level='INFO') as captured:
            # assertLogs demands at least one record, so emit a marker and
            # assert it is the only one.
            logging.getLogger('search').info('marker')
            self.client.get(self.url, {'q': ''})
        self.assertEqual([r.getMessage() for r in captured.records], ['marker'])


class SearchLoggingSettingsTestCase(TestCase):
    """
    Where search logging is configured to land.

    Asserted against the settings modules rather than the running logger: the
    suite runs under `test`, which configures no such logger, so the only way
    to cover the requirement is to read the configuration the site deploys.

    """
    def settings_modules(self):
        from sg101.settings import local, production
        return {'local': local.LOGGING, 'production': production.LOGGING}

    def test_search_gets_its_own_file(self):
        for name, config in self.settings_modules().items():
            with self.subTest(settings=name):
                handler = config['handlers']['search']
                self.assertTrue(handler['filename'].endswith('search.log'))

    def test_search_does_not_reach_the_site_log(self):
        # propagate False is what keeps the root logger, and so sg101.log,
        # from collecting a copy of every search.
        for name, config in self.settings_modules().items():
            with self.subTest(settings=name):
                logger_config = config['loggers']['search']
                self.assertFalse(logger_config['propagate'])
                self.assertEqual(logger_config['handlers'], ['search'])


class SearchRoutesTestCase(TestCase):
    """The rename off the dead haystack_* names."""

    def test_the_search_route_keeps_its_url(self):
        self.assertEqual(reverse('search'), '/search/')

    def test_the_ajax_route_keeps_its_url(self):
        self.assertEqual(reverse('search_ajax'), '/search/ajax/')

    def test_no_haystack_route_names_remain(self):
        from django.urls import NoReverseMatch
        for name in ['haystack_search', 'haystack_search_ajax']:
            with self.subTest(name=name):
                with self.assertRaises(NoReverseMatch):
                    reverse(name)
