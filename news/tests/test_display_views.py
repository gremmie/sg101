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

    def test_tag_page_differing_case_redirects_to_the_canonical_url(self):
        """Tags are stored lowercased, so every case variant names the same
        page. Serving it at both would give one page two URLs and a heading
        echoing whatever casing the visitor happened to type."""
        self.story.tags = ['surf']
        self.story.save()

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Surf'}))

        self.assertRedirects(
            response, reverse('news-tag_page', kwargs={'tag_name': 'surf'}),
            status_code=301)

    def test_tag_page_differing_case_still_reaches_the_stories(self):
        self.story.tags = ['surf']
        self.story.save()

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Surf'}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_the_canonical_redirect_keeps_the_page_number(self):
        """The tag page is paginated; dropping the query string would send a
        visitor on page 4 back to page 1."""
        self.story.tags = ['surf']
        self.story.save()

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Surf'}) + '?page=2')

        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].endswith('/news/tag/surf/?page=2'),
                        response['Location'])

    def test_a_lowercase_tag_url_does_not_redirect(self):
        self.story.tags = ['surf']
        self.story.save()

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'surf'}))

        self.assertEqual(response.status_code, 200)

    def test_a_mixed_case_unknown_tag_redirects_and_then_404s(self):
        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Nonexistent'}),
            follow=True)

        self.assertEqual(response.status_code, 404)

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
        """Every tag URL resolves against the lowercase name, so a tag stored
        with a capital in it would be unreachable. django-tagging did this with
        FORCE_LOWERCASE_TAGS, which is why all 1,006 production tags are
        lowercase with no case variants; the model has to keep doing it."""
        self.story.tags = ['Surf', 'REVERB']
        self.story.save()
        self.story.refresh_from_db()

        self.assertEqual(self.story.tags, ['surf', 'reverb'])

        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Surf'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())
