"""Unit tests for the news app."""

import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.utils import timezone

from news.models import Category, PendingStory, Story


class NewsTestCase(TestCase):

    def setUp(self):
        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username, password=self.pw))

    def tearDown(self):
        pass


class SubmitViewTestCase(NewsTestCase):

    fixtures = ['news_categories.json']

    def setUp(self):
        super(SubmitViewTestCase, self).setUp()
        self.view_url = reverse('news-submit')

    def test_get(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        args = {
            'title': 'My news story',
            'category': '1',
            'short_markup': "Here is the story text.",
        }
        now = timezone.now()
        response = self.client.post(self.view_url, args, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain,
                         [(reverse('news-submit_thanks'), 302)])

        stories = list(PendingStory.objects.all())
        self.assertEqual(len(stories), 1)
        story = stories[0]
        self.assertEqual(story.submitter, self.user)
        self.assertEqual(story.title, args['title'])
        self.assertEqual(story.short_markup, args['short_markup'])
        self.assertTrue(now - story.date_submitted < datetime.timedelta(seconds=2))
        self.assertTrue(now - story.update_date < datetime.timedelta(seconds=2))
        self.assertEqual(story.category.pk, 1)
        self.assertEqual(story.long_markup, '')
        self.assertEqual(story.long_text, '')
        self.assertEqual(story.short_text, '<p>{}</p>'.format(args['short_markup']))

    def test_post_with_bad_image(self):
        args = {
            'title': 'My news story',
            'category': '1',
            'short_markup': "Image: ![image](http://example.com/a.jpg)\n",
        }
        response = self.client.post(self.view_url, args, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Image must be accessed via https' in response.content.decode())
        self.assertEqual(response.redirect_chain, [])

        stories = list(PendingStory.objects.all())
        self.assertEqual(len(stories), 0)


class ArchiveMonthBoundaryTestCase(TestCase):
    """
    The news archive groups stories by month, so a story submitted in the
    evening on the last day of a month is one timezone away from being filed
    under the next one. Nothing raises when that happens -- the month page is
    simply missing a story and the archive index may gain a month.
    """
    fixtures = ['news_categories.json']

    def setUp(self):
        self.user = User.objects.create_user('archivist', '', 'pw')
        self.category = Category.objects.get(pk=1)
        # 7pm Chicago on the last day of January; 01:00 UTC on February 1st.
        submitted = datetime.datetime(2026, 1, 31, 19, 0,
                                      tzinfo=ZoneInfo('America/Chicago'))
        self.story = Story.objects.create(
                title='Late January story', submitter=self.user,
                category=self.category, date_submitted=submitted,
                update_date=submitted)
        # Story.save() stamps date_submitted with now() on insert, so the
        # wanted value has to go in behind it.
        Story.objects.filter(pk=self.story.pk).update(date_submitted=submitted,
                                                      update_date=submitted)
        self.story.refresh_from_db()

    def test_the_story_is_stored_in_the_next_utc_month(self):
        """Guard the premise, so the tests below cannot pass vacuously."""
        stored = self.story.date_submitted.astimezone(datetime.timezone.utc)
        self.assertEqual((stored.year, stored.month, stored.day), (2026, 2, 1))

    def test_the_archive_page_files_it_under_january(self):
        resp = self.client.get(reverse('news-archive_page',
                                       args=['2026', '01']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Late January story')

    def test_the_archive_index_lists_january_not_february(self):
        resp = self.client.get(reverse('news-archive_index'))
        self.assertEqual(resp.status_code, 200)
        months = [(d.year, d.month) for d in resp.context['dates']]
        self.assertIn((2026, 1), months)
        self.assertNotIn((2026, 2), months)

    def test_neither_follows_an_activated_timezone(self):
        for name in ['UTC', 'US/Pacific', 'Australia/Sydney']:
            with self.subTest(tz=name), timezone.override(name):
                resp = self.client.get(reverse('news-archive_page',
                                               args=['2026', '01']))
                self.assertContains(resp, 'Late January story')

                resp = self.client.get(reverse('news-archive_index'))
                months = [(d.year, d.month) for d in resp.context['dates']]
                self.assertIn((2026, 1), months)
                self.assertNotIn((2026, 2), months)
