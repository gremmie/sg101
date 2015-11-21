"""Unit tests for the news app."""

import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from news.models import PendingStory


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
        now = datetime.datetime.now()
        response = self.client.post(self.view_url, args, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain,
                         [('http://testserver' + reverse('news-submit_thanks'), 302)])

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
        self.assertTrue('Image must be accessed via https' in response.content)
        self.assertEqual(response.redirect_chain, [])

        stories = list(PendingStory.objects.all())
        self.assertEqual(len(stories), 0)
