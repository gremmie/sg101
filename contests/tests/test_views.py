"""
View tests for the contests application.

"""
import datetime
import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from contests.models import Contest


class NoConstestsTestCase(TestCase):

    def test_no_contests(self):
        response = self.client.get(reverse('contests-index'))
        self.assertEqual(response.status_code, 200)

        url = reverse('contests-contest', kwargs={'slug': 'test'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ConstestsTestCase(TestCase):

    def setUp(self):
        now = datetime.datetime.now()
        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        user = User.objects.create_user('test_user', '', 'password')
        user.save()

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end,
                win_date=end + datetime.timedelta(days=1),
                num_winners=1)
        c.save()
        c.contestants.add(user)
        c.winners.add(user)
        self.contest_id = c.id

    def test_contests(self):
        response = self.client.get(reverse('contests-index'))
        self.assertEqual(response.status_code, 200)

        url = reverse('contests-contest', kwargs={'slug': 'test'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ContestEntryTestCase(TestCase):

    def setUp(self):
        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username,
            password=self.pw))

        now = datetime.datetime.now()
        start = now - datetime.timedelta(days=7)
        end = now + datetime.timedelta(days=3)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end,
                num_winners=1)
        c.save()
        self.contest_id = c.id

    def test_entry_toggle(self):
        response = self.client.post(reverse('contests-enter'),
                {'contest_id': self.contest_id},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        c = json.loads(response.content)
        self.assertTrue(c['entered'])

        contest = Contest.objects.get(pk=self.contest_id)
        self.assertTrue(self.user in contest.contestants.all())

        response = self.client.post(reverse('contests-enter'),
                {'contest_id': self.contest_id},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        c = json.loads(response.content)
        self.assertFalse(c['entered'])

        contest = Contest.objects.get(pk=self.contest_id)
        self.assertFalse(self.user in contest.contestants.all())


class NoPublicConstestsTestCase(TestCase):

    def setUp(self):
        now = datetime.datetime.now()
        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=False,
                creation_date=start,
                end_date=end)
        c.save()

    def test_contests(self):
        response = self.client.get(reverse('contests-index'))
        self.assertEqual(response.status_code, 200)

        url = reverse('contests-contest', kwargs={'slug': 'test'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
