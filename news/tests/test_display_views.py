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

from tagging.models import Tag

from news.models import Category, Story


def make_story(submitter, category, title='A News Story', markup='story body'):
    return Story.objects.create(title=title, submitter=submitter,
                                category=category, short_markup=markup)


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
        Tag.objects.update_tags(self.story, 'surf')
        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'surf'}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_tag_page_differing_case(self):
        Tag.objects.update_tags(self.story, 'surf')
        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'Surf'}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Front Page News', response.content.decode())

    def test_unknown_tag_is_404(self):
        response = self.client.get(
            reverse('news-tag_page', kwargs={'tag_name': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)

    def test_tagging_is_case_normalized(self):
        """A case variant must reuse the existing tag, not create a second.

        django-tagging looks tags up with get_or_create(name=...), which is
        case-sensitive on any engine but MySQL. What saves us is
        FORCE_LOWERCASE_TAGS, which lowercases the name first -- hence 1,006
        tags in production with no case variants among them. Pinned here
        because turning that setting off would quietly start splitting tags in
        two once we are on Postgres.

        """
        Tag.objects.update_tags(self.story, 'surf')
        Tag.objects.add_tag(self.story, 'Surf')

        self.assertEqual(Tag.objects.filter(name__iexact='surf').count(), 1)
        self.assertEqual(list(Tag.objects.values_list('name', flat=True)),
                         ['surf'])


class NewsEmailStoryTests(TestCase):
    fixtures = ['news_categories.json']

    def setUp(self):
        self.author = User.objects.create_user('author', '', 'pw')
        self.reader = User.objects.create_user('reader', 'reader@example.com', 'pw')
        self.story = make_story(self.author, Category.objects.get(pk=1))

    def test_email_story_requires_login(self):
        response = self.client.get(reverse('news-email_story', args=[self.story.id]))
        self.assertEqual(response.status_code, 302)

    def test_email_story_form_renders(self):
        self.client.login(username='reader', password='pw')
        response = self.client.get(reverse('news-email_story', args=[self.story.id]))
        self.assertEqual(response.status_code, 200)

    def test_email_story_sends_mail(self):
        self.client.login(username='reader', password='pw')
        response = self.client.post(
            reverse('news-email_story', args=[self.story.id]),
            {'friend_name': 'A Friend', 'friend_email': 'friend@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('friend@example.com', mail.outbox[0].to)

    def test_email_thanks_renders(self):
        self.client.login(username='reader', password='pw')
        response = self.client.get(reverse('news-email_thanks', args=[self.story.id]))
        self.assertEqual(response.status_code, 200)
