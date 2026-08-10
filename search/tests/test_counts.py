"""
Tests for the per-type result counts on the search page.

Both ways these counts go wrong -- an ordering left on the queryset before the
aggregate, and grouping on a model name two apps share -- return numbers rather
than errors, and the numbers look entirely reasonable on their own. So the
counts are checked against what a search for that one type actually returns
rather than against expected constants, per type, every time.

"""
import datetime

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from downloads.models import Category as DownloadCategory
from downloads.models import Download
from forums.models import Category
from forums.models import Forum
from forums.models import Post
from forums.models import Topic
from search.documents import all_documents
from search.forms import SearchForm
from search.models import SearchDocument
from search.query import search_documents
from search.query import type_counts
from ygroup.models import Post as YgroupPost


class TypeCountsTestCase(TestCase):
    """
    A corpus with different numbers of each type, so a count that comes back
    right by coincidence has somewhere to go wrong.

    """
    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.url = reverse('search')
        self.keys = [document.key for document in all_documents()]

        # Three topics, each with two posts: six forum posts against three
        # topics, so the two cannot be confused for one another.
        for n in range(3):
            topic = Topic.objects.create(forum=self.forum, user=self.user,
                                         name='Reverb tank %d' % n)
            SearchDocument.objects.index_object(topic)
            for m in range(2):
                post = Post.objects.create(topic=topic, user=self.user,
                                           body='Reverb notes %d-%d' % (n, m))
                SearchDocument.objects.index_object(post)

        # Two archive posts. These share the model name "post" with the forums,
        # which is the collision the grouping has to survive.
        for n in range(2):
            SearchDocument.objects.index_object(YgroupPost.objects.create(
                    title='Reverb thread %d' % n, poster='wahini',
                    msg='Old reverb talk',
                    creation_date=timezone.make_aware(
                            datetime.datetime(2005, 3, 1, 12, 0))))

        # One download, and nothing at all for the remaining types.
        SearchDocument.objects.index_object(Download.objects.create(
                category=DownloadCategory.objects.create(title='Tabs',
                                                         slug='tabs'),
                title='Reverb tab', description='A tab.',
                file='downloads/reverb.txt', user=self.user,
                ip_address='127.0.0.1', is_public=True))

    def login(self):
        self.assertTrue(self.client.login(username='kahuna', password='pw'))

    # -- the counts themselves -------------------------------------------

    def test_each_count_equals_a_search_for_that_type_alone(self):
        counts = type_counts('reverb')

        for key in self.keys:
            with self.subTest(key=key):
                self.assertEqual(counts[key],
                                 search_documents('reverb', [key]).count())

    def test_the_counts_are_the_numbers_seeded(self):
        # The assertion above would pass if both sides were wrong the same way.
        counts = type_counts('reverb')

        self.assertEqual(counts['forums.topic'], 3)
        self.assertEqual(counts['forums.post'], 6)
        self.assertEqual(counts['ygroup.post'], 2)
        self.assertEqual(counts['downloads.download'], 1)

    def test_the_two_post_types_are_counted_apart(self):
        # forums.Post and ygroup.Post are both "post"; grouping on the model
        # name merges them and reports 8 against each.
        counts = type_counts('reverb')

        self.assertNotEqual(counts['forums.post'], counts['ygroup.post'])
        self.assertEqual(counts['forums.post'] + counts['ygroup.post'], 8)

    def test_no_count_comes_back_as_one(self):
        # An ordering surviving into the GROUP BY makes every row its own
        # group, so every count is 1 -- individually plausible for a small
        # corpus, which is why this is asserted directly.
        counts = type_counts('reverb')

        self.assertNotEqual(list(counts.values()), [1] * len(self.keys))
        self.assertEqual(counts['forums.post'], 6)

    def test_every_type_is_present_including_the_empty_ones(self):
        counts = type_counts('reverb')

        self.assertEqual(list(counts), self.keys)
        self.assertEqual(counts['news.story'], 0)
        self.assertEqual(counts['weblinks.link'], 0)
        self.assertEqual(counts['podcast.item'], 0)

    def test_the_counts_sum_to_the_total(self):
        counts = type_counts('reverb')

        self.assertEqual(sum(counts.values()),
                         search_documents('reverb', self.keys).count())

    def test_a_query_matching_nothing_counts_every_type_zero(self):
        counts = type_counts('xyzzy')

        self.assertEqual(list(counts), self.keys)
        self.assertEqual(set(counts.values()), {0})

    # -- independence from the current selection -------------------------

    def test_narrowing_to_one_type_leaves_the_other_counts_intact(self):
        self.login()

        response = self.client.get(self.url, {'q': 'reverb',
                                              'models': ['forums.topic']})

        labels = self.choice_labels(response)
        self.assertIn('Forum Topics (3)', labels)
        # The counts a member needs in order to change their mind.
        self.assertIn('Forum Posts (6)', labels)
        self.assertIn('Yahoo Group Archives (2)', labels)

    # -- what the page renders -------------------------------------------

    def choice_labels(self, response):
        return [label for _, label
                in response.context['form'].fields['models'].choices]

    def test_the_counts_render_beside_the_checkboxes(self):
        self.login()

        response = self.client.get(self.url, {'q': 'reverb'})

        self.assertContains(response, 'Forum Posts (6)')
        self.assertContains(response, 'Downloads (1)')
        self.assertContains(response, 'News Stories (0)')

    def test_large_counts_are_grouped_for_reading(self):
        # Six figures of forum posts is the realistic case, and 137983 is
        # harder to read at a glance than 137,983.
        form = SearchForm()
        form.show_counts({key: 0 for key in self.keys})
        form.show_counts(dict({key: 0 for key in self.keys},
                              **{'forums.post': 137983}))

        self.assertIn(('forums.post', 'Forum Posts (137,983)'),
                      form.fields['models'].choices)

    def test_the_landing_page_carries_no_counts(self):
        self.login()

        response = self.client.get(self.url)

        for label in self.choice_labels(response):
            self.assertNotIn('(', label)

    def test_a_rejected_query_carries_no_counts(self):
        self.login()

        response = self.client.get(self.url, {'q': ''})

        self.assertFalse(response.context['form'].is_valid())
        for label in self.choice_labels(response):
            self.assertNotIn('(', label)

    # -- the headline total ----------------------------------------------

    def test_the_hit_count_covers_only_the_selected_types(self):
        self.login()

        response = self.client.get(self.url, {'q': 'reverb',
                                              'models': ['forums.topic']})

        self.assertEqual(response.context['page'].paginator.count, 3)

    def test_the_hit_count_spans_several_selected_types(self):
        self.login()

        response = self.client.get(
                self.url,
                {'q': 'reverb', 'models': ['forums.post', 'ygroup.post']})

        self.assertEqual(response.context['page'].paginator.count, 8)

    def test_an_unnarrowed_search_counts_everything(self):
        self.login()

        response = self.client.get(self.url, {'q': 'reverb'})

        self.assertEqual(response.context['page'].paginator.count, 12)

    def test_the_paginator_total_agrees_with_the_rows_it_pages(self):
        self.login()

        response = self.client.get(self.url, {'q': 'reverb'})

        paginator = response.context['page'].paginator
        self.assertEqual(paginator.count, len(paginator.object_list))

    # -- cost --------------------------------------------------------------

    def test_the_paginator_issues_no_count_of_its_own(self):
        self.login()

        with CaptureQueriesContext(connection) as queries:
            self.client.get(self.url, {'q': 'reverb'})

        index = [q['sql'] for q in queries.captured_queries
                 if 'search_searchdocument' in q['sql']]
        # One aggregate -- the facets -- and no second pass counting the same
        # rows again. Getting the total from the facets is what keeps a search
        # at two statements rather than three.
        self.assertEqual(len([sql for sql in index if 'GROUP BY' in sql]), 1)
        self.assertEqual(
                [sql for sql in index
                 if 'COUNT(' in sql.upper() and 'GROUP BY' not in sql], [])

    def test_a_search_costs_the_same_two_statements_as_the_rows_it_shows(self):
        self.login()

        with CaptureQueriesContext(connection) as queries:
            self.client.get(self.url, {'q': 'reverb'})

        index = [q['sql'] for q in queries.captured_queries
                 if 'search_searchdocument' in q['sql']]
        self.assertEqual(len(index), 2)
