"""Tests for the weblinks add-link form."""

from django.contrib.auth.models import User
from django.test import TestCase

from weblinks.forms import AddLinkForm
from weblinks.models import Category
from weblinks.models import Link


class AddLinkFormTestCase(TestCase):
    """How the member-facing add-link form treats what was typed in the url box.

    Rejecting bad input is not what the form field buys: the model field
    underneath validates too, through ModelForm._post_clean, so gibberish and a
    javascript: scheme were refused either way. What it buys is the scheme-less
    case -- a bare domain is normalized rather than refused with an error that
    does not say what to fix.

    """
    fixtures = ['weblinks_categories.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')
        self.category = Category.objects.get(pk=1)

    def form(self, url):
        return AddLinkForm({'category': self.category.pk,
                            'title': 'Title',
                            'url': url,
                            'description': 'Cool stuff'})

    def existing_link(self, url):
        return Link.objects.create(category=self.category, title='Existing',
                                   url=url, user=self.user)

    def test_a_bare_domain_is_accepted_and_given_a_scheme(self):
        form = self.form('example.com')

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data['url'], 'https://example.com')

    def test_a_url_that_already_has_a_scheme_is_left_alone(self):
        form = self.form('http://example.com/page')

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data['url'], 'http://example.com/page')

    def test_gibberish_is_rejected(self):
        form = self.form('not a url at all')

        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)

    def test_a_javascript_url_is_rejected(self):
        form = self.form('javascript:alert(1)')

        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)

    def test_a_bare_domain_reaches_the_duplicate_check(self):
        """What clean_url compares is the normalized value, not what was typed.

        Field cleaning runs first, so a bare domain that used to fail validation
        before any duplicate check happened now arrives at one.

        """
        self.existing_link('https://example.com')

        form = self.form('example.com')

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['url'],
                         ['That link already exists in our database.'])

    def test_a_link_stored_on_another_scheme_is_not_a_duplicate(self):
        """The check is an exact match after normalization, and stays one.

        Most stored links are http, a bare domain normalizes to https, and
        url__iexact does not bridge the two. Pinned rather than widened: the
        same is true of a trailing slash, and deciding what counts as the same
        link is a larger question than the url box.

        """
        self.existing_link('http://example.com')

        form = self.form('example.com')

        self.assertTrue(form.is_valid(), msg=form.errors)
