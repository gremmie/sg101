"""Tests for running a search: term parsing, ranking and snippets."""

import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from forums.models import Category
from forums.models import Forum
from forums.models import Post
from forums.models import Topic
from news.models import Category as NewsCategory
from news.models import Story
from search.models import SearchDocument
from search.query import positive_terms
from search.query import search_documents


class PositiveTermsTestCase(TestCase):
    """
    What survives for the ranking query once exclusions are dropped.

    ts_rank returns the same constant for every row the moment its tsquery
    holds a negated term, so ranking runs against this reduced string while
    filtering keeps the whole one.

    """
    def test_a_query_without_exclusions_is_unchanged(self):
        self.assertEqual(positive_terms('fender jaguar'), 'fender jaguar')

    def test_an_excluded_word_is_dropped(self):
        self.assertEqual(positive_terms('reverb -fender'), 'reverb')

    def test_an_excluded_phrase_is_dropped_whole(self):
        self.assertEqual(positive_terms('reverb -"fender twin"'), 'reverb')

    def test_a_quoted_phrase_survives_with_its_quotes(self):
        self.assertEqual(positive_terms('"surf music" -disco'), '"surf music"')

    def test_a_phrase_containing_a_hyphenated_word_is_not_split(self):
        self.assertEqual(positive_terms('"fender-made amps"'),
                         '"fender-made amps"')

    def test_an_interior_hyphen_does_not_exclude(self):
        # Only a leading '-' excludes; websearch reads the rest as one word.
        self.assertEqual(positive_terms('surf-music'), 'surf-music')

    def test_extra_whitespace_collapses(self):
        self.assertEqual(positive_terms('  reverb   -fender  '), 'reverb')

    def test_an_unclosed_quote_runs_to_the_end(self):
        self.assertEqual(positive_terms('"surf music'), '"surf music')

    def test_a_query_of_only_exclusions_reduces_to_nothing(self):
        self.assertEqual(positive_terms('-fender -gibson'), '')


class SearchDocumentsTestCase(TestCase):
    """Ranking and filtering against a small hand-built index."""

    ALL_KEYS = ['forums.topic', 'forums.post', 'news.story']

    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.forum = Forum.objects.create(
                category=Category.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.news_category = NewsCategory.objects.create(title='Site News',
                                                         slug='site-news')

    def index_topic(self, name):
        topic = Topic.objects.create(forum=self.forum, user=self.user,
                                     name=name)
        return SearchDocument.objects.index_object(topic)

    def index_post(self, topic_name, body):
        topic = Topic.objects.create(forum=self.forum, user=self.user,
                                     name=topic_name)
        post = Post.objects.create(topic=topic, user=self.user, body=body)
        return SearchDocument.objects.index_object(post)

    def index_story(self, title, short_text=''):
        story = Story.objects.create(title=title, submitter=self.user,
                                     category=self.news_category,
                                     short_text=short_text, long_text='')
        return SearchDocument.objects.index_object(story)

    def titles(self, query, keys=None):
        keys = self.ALL_KEYS if keys is None else keys
        return [row.title for row in search_documents(query, keys)]

    def test_a_matching_document_is_found(self):
        self.index_topic('Fender Jaguar setup')
        self.assertEqual(self.titles('jaguar'), ['Fender Jaguar setup'])

    def test_several_words_require_all_of_them(self):
        self.index_topic('Fender Jaguar setup')
        self.index_topic('Fender Jazzmaster setup')
        self.assertEqual(self.titles('fender jaguar'), ['Fender Jaguar setup'])

    def test_a_quoted_phrase_requires_the_words_adjacent(self):
        self.index_topic('Surf music forever')
        # Holds both words, but not next to each other -- so a phrase search
        # must reject it where a plain two-word search would not.
        self.index_topic('Music from the surf scene')
        self.assertEqual(self.titles('"surf music"'), ['Surf music forever'])

    def test_an_excluded_word_removes_its_documents(self):
        self.index_topic('Reverb tank rebuild')
        self.index_topic('Reverb into a Fender amp')
        self.assertEqual(self.titles('reverb -fender'),
                         ['Reverb tank rebuild'])

    def test_a_title_hit_outranks_a_body_hit(self):
        # Weight A over weight B, which is the whole point of the weighting:
        # the story names the term, the post merely mentions it at length.
        self.index_story('Dick Dale in concert')
        self.index_post('Amp settings',
                        'A long post about amps. ' * 40 + 'Dick Dale played.')
        self.assertEqual(self.titles('dick dale')[0], 'Dick Dale in concert')

    def test_ranking_survives_an_exclusion(self):
        # The regression this file's positive_terms() exists for: with the
        # exclusion in the ranking query every row scores the same constant,
        # and the title hit stops sorting first.
        self.index_story('Reverb explained')
        self.index_post('Amp settings',
                        'Plenty of prose here. ' * 40 + 'Some reverb talk.')
        self.assertEqual(self.titles('reverb -gibson')[0], 'Reverb explained')

    def test_results_are_ordered_by_rank_not_date(self):
        older = self.index_story('Reverb explained')
        newer = self.index_post('Chat', 'Just a passing mention of reverb.')
        SearchDocument.objects.filter(pk=older.pk).update(
                date=datetime.datetime(2001, 1, 1))
        SearchDocument.objects.filter(pk=newer.pk).update(
                date=datetime.datetime(2026, 1, 1))
        self.assertEqual(self.titles('reverb')[0], 'Reverb explained')

    def test_equal_scores_break_towards_the_newer_document(self):
        first = self.index_topic('Reverb')
        second = self.index_topic('Reverb')
        SearchDocument.objects.filter(pk=first.pk).update(
                date=datetime.datetime(2001, 1, 1))
        SearchDocument.objects.filter(pk=second.pk).update(
                date=datetime.datetime(2026, 1, 1))
        results = list(search_documents('reverb', self.ALL_KEYS))
        self.assertEqual([row.pk for row in results], [second.pk, first.pk])

    def test_only_the_named_types_are_searched(self):
        self.index_topic('Reverb topic')
        self.index_story('Reverb story')
        self.assertEqual(self.titles('reverb', ['news.story']),
                         ['Reverb story'])

    def test_a_hyphenated_model_number_is_found_as_written(self):
        # The old search tips apologised that FRV-1 found nothing, because
        # Xapian dropped punctuation when indexing. PostgreSQL's parser splits
        # the token but keeps the halves adjacent, and reads the query as a
        # phrase over them, so it matches. The tip went with this test.
        self.index_topic('Boss FRV-1 pedal review')
        self.assertEqual(self.titles('FRV-1'), ['Boss FRV-1 pedal review'])

    def test_a_hyphenated_word_is_found_either_way(self):
        # A hyphenated word indexes as the compound and as both halves.
        self.index_topic('For the surf-music faithful')
        for query in ['surf-music', 'surf music', 'music']:
            with self.subTest(query=query):
                self.assertEqual(self.titles(query),
                                 ['For the surf-music faithful'])

    def test_a_query_of_only_exclusions_still_runs(self):
        # positive_terms() reduces this to an empty ranking query, which ranks
        # every row equally and leaves the date tiebreak to order them. The
        # filter still means what it says: everything without the word.
        self.index_topic('Reverb tank rebuild')
        self.index_topic('Fender amp advice')
        self.assertEqual(self.titles('-fender'), ['Reverb tank rebuild'])

    def test_malformed_input_returns_results_rather_than_raising(self):
        # The old Xapian parser raised on input like this, which is what the
        # deleted view's QueryParserError branch existed to catch.
        self.index_topic('Reverb tank rebuild')
        for query in ['reverb AND', '"unclosed', ')(', 'reverb OR OR']:
            with self.subTest(query=query):
                list(search_documents(query, self.ALL_KEYS))

    def test_a_snippet_marks_the_matched_words(self):
        self.index_post('Amp settings', 'The reverb tank needs a rebuild.')
        row = search_documents('reverb', self.ALL_KEYS)[0]
        self.assertIn('<span class="highlight">reverb</span>', row.highlighted)

    def test_a_snippet_escapes_the_text_around_the_match(self):
        # A summary is plain text that can hold angle brackets: body_text()
        # unescapes what it strips tags from, so stored `&lt;` -- which is how
        # every news story and much of the ygroup archive holds a typed '<' --
        # arrives here as a live tag. ts_headline drops some tags but by no
        # means all: this payload comes back through it intact, so publishing
        # a headline as HTML would be stored XSS.
        self.index_post('Amp settings',
                        'Look &lt;img src=x onerror=alert(1)&gt; reverb.')
        row = search_documents('reverb', self.ALL_KEYS)[0]
        self.assertNotIn('<img', row.highlighted)
        self.assertIn('&lt;img', row.highlighted)

    def test_a_snippet_keeps_a_bare_angle_bracket_readable(self):
        # Escaping has to survive round-tripping too: 'a < b' is prose, not
        # markup, and should read as it was written.
        self.index_post('Amp settings', 'When a &lt; b the reverb wins.')
        row = search_documents('reverb', self.ALL_KEYS)[0]
        self.assertIn('a &lt; b', row.highlighted)

    def test_a_result_row_names_its_own_type(self):
        self.index_topic('Reverb tank rebuild')
        row = search_documents('reverb', self.ALL_KEYS)[0]
        self.assertEqual(row.result_label, 'Forum Topic')
