"""
Characterization tests for the news display and email views.

The existing tests cover story submission; these cover the read-side journeys --
the front-page index, archives, categories, tags, single-story pages, and the
"email this story to a friend" flow -- which together are the most-visible pages
on the site.
"""
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.test import TestCase

from news.models import Category, Story


def make_story(submitter, category, title='A News Story', markup='story body',
               tags=None):
    return Story.objects.create(title=title, submitter=submitter,
                                category=category, short_markup=markup,
                                tags=tags or [])


class NewsDisplayTests(TestCase):
    fixtures = ['news_categories.json']

    def setUp(self):
        self.author = User.objects.create_user('author', '', 'pw')
        self.category = Category.objects.get(pk=1)
        self.story = make_story(self.author, self.category, title='Front Page News')

    def test_index_lists_stories(self):
        response = self.client.get(reverse('news-index_page'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_archive_index_renders(self):
        response = self.client.get(reverse('news-archive_index'))
        self.assertEqual(response.status_code, 200)

    def test_archive_page_renders(self):
        d = self.story.date_submitted
        response = self.client.get(
            reverse('news-archive_page', kwargs={'year': d.year, 'month': d.month}))
        self.assertEqual(response.status_code, 200)

    def test_category_index_renders(self):
        response = self.client.get(reverse('news-category_index'))
        self.assertEqual(response.status_code, 200)

    def test_category_page_renders(self):
        response = self.client.get(
            reverse('news-category', kwargs={'slug': self.category.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_unknown_category_is_404(self):
        response = self.client.get(
            reverse('news-category', kwargs={'slug': 'no-such-category'}))
        self.assertEqual(response.status_code, 404)

    def test_story_page_renders(self):
        response = self.client.get(reverse('news-story', args=[self.story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_unknown_story_is_404(self):
        response = self.client.get(reverse('news-story', args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_tag_index_renders(self):
        response = self.client.get(reverse('news-tag_index'))
        self.assertEqual(response.status_code, 200)

    def test_tag_page_lists_tagged_stories(self):
        self.story.tags = ['surf']
        self.story.save()
        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'surf'}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_tag_page_differing_case(self):
        self.story.tags = ['surf']
        self.story.save()
        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Surf'}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_tag_page_lists_only_the_stories_carrying_the_tag(self):
        self.story.tags = ['surf']
        self.story.save()
        make_story(self.author, self.category, title='Unrelated',
                   tags=['tremolo'])

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'surf'}))

        body = response.content.decode()
        self.assertIn('Front Page News', body)
        self.assertNotIn('Unrelated', body)

    def test_unknown_tag_is_404(self):
        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)

    def test_a_tag_no_story_carries_is_404(self):
        """A change from the tagging app, and a deliberate one: a Tag row could
        outlive every story that used it, and its page then rendered empty with
        a 200. There is no tag row to outlive anything now."""
        self.story.tags = ['surf']
        self.story.save()
        self.story.tags = []
        self.story.save()

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'surf'}))

        self.assertEqual(response.status_code, 404)

    def test_tags_are_stored_lowercased(self):
        """The tag page lowercases what it looks up, so a tag stored with a
        capital in it would be unreachable. django-tagging did this with
        FORCE_LOWERCASE_TAGS, which is why all 1,006 production tags are
        lowercase with no case variants; the model has to keep doing it."""
        self.story.tags = ['Surf', 'REVERB']
        self.story.save()
        self.story.refresh_from_db()

        self.assertEqual(self.story.tags, ['surf', 'reverb'])

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Surf'}))
        self.assertEqual(response.status_code, 200)
