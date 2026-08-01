"""Tests for the search form."""

from django.test import TestCase

from search.forms import SearchForm


ALL_KEYS = ['forums.topic', 'forums.post', 'news.story', 'bio.userprofile',
            'weblinks.link', 'downloads.download', 'podcast.item',
            'ygroup.post']


class SearchFormTestCase(TestCase):

    def test_the_type_choices_are_the_recovered_labels_in_order(self):
        # Verbatim from the deleted form's MODEL_CHOICES, which is what
        # members are used to reading down.
        self.assertEqual(
                [label for _, label in SearchForm().fields['models'].choices],
                ['Forum Topics', 'Forum Posts', 'News Stories',
                 'User Profiles', 'Links', 'Downloads', 'Podcasts',
                 'Yahoo Group Archives'])

    def test_the_type_keys_match_the_old_search_urls(self):
        self.assertEqual(
                [key for key, _ in SearchForm().fields['models'].choices],
                ALL_KEYS)

    def test_no_box_starts_checked(self):
        # A member picks their areas rather than being handed a whole-site
        # search. Submitting with none checked still means everything, which
        # clean_models covers below.
        self.assertFalse(SearchForm().fields['models'].initial)
        self.assertNotIn('checked', str(SearchForm()['models']))

    def test_an_empty_query_is_rejected_with_the_recovered_message(self):
        form = SearchForm({'q': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('Please supply some search terms', form.errors['q'])

    def test_a_whitespace_only_query_is_rejected(self):
        form = SearchForm({'q': '   '})
        self.assertFalse(form.is_valid())

    def test_a_query_alone_searches_every_type(self):
        # The masthead box in v3/base.html posts a bare q, and a browser sends
        # nothing at all for a checkbox group with no box checked. The two are
        # indistinguishable, so both mean everything.
        form = SearchForm({'q': 'reverb'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['models'], ALL_KEYS)

    def test_checked_types_are_kept(self):
        form = SearchForm({'q': 'reverb', 'models': ['news.story']})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['models'], ['news.story'])

    def test_an_unknown_type_is_rejected(self):
        form = SearchForm({'q': 'reverb', 'models': ['forums.nonesuch']})
        self.assertFalse(form.is_valid())
