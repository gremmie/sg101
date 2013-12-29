"""
Model tests for the contests application.

"""
import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from contests.models import Contest


class ContestTestCase(TestCase):

    def test_creation_date(self):

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=False,
                end_date=datetime.datetime.now() + datetime.timedelta(days=30))

        c.save()

        self.assertTrue(c.creation_date)
        self.assertTrue(datetime.datetime.now() - c.creation_date <
                datetime.timedelta(seconds=1))

    def test_is_active(self):

        now = datetime.datetime.now()
        start = now + datetime.timedelta(days=7)
        end = start + datetime.timedelta(days=30)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=False,
                creation_date=start,
                end_date=end)

        self.assertFalse(c.is_active())

        start = now - datetime.timedelta(days=7)
        end = start + datetime.timedelta(days=30)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end)

        self.assertTrue(c.is_active())

        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end)

        self.assertFalse(c.is_active())

    def test_can_enter(self):

        now = datetime.datetime.now()
        start = now + datetime.timedelta(days=7)
        end = start + datetime.timedelta(days=30)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=False,
                creation_date=start,
                end_date=end)

        self.assertFalse(c.can_enter())

        start = now - datetime.timedelta(days=7)
        end = start + datetime.timedelta(days=30)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end)

        self.assertTrue(c.can_enter())

        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end)

        self.assertFalse(c.can_enter())

        start = now - datetime.timedelta(days=7)
        end = start + datetime.timedelta(days=30)

        user = User.objects.create_user('test_user', '', 'password')
        user.save()

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end,
                winner=user,
                win_date=now)

        self.assertFalse(c.can_enter())

        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=True,
                creation_date=start,
                end_date=end,
                winner=user,
                win_date=end + datetime.timedelta(days=1))

        self.assertFalse(c.can_enter())

    def test_pick_winner(self):

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

        user1 = User.objects.create_user('test_user1', '', 'password')
        user1.save()
        user2 = User.objects.create_user('test_user2', '', 'password')
        user2.save()
        user3 = User.objects.create_user('test_user3', '', 'password')
        user3.save()

        c.contestants.add(user1, user2, user3)

        c.pick_winner()

        self.assertTrue(datetime.datetime.now() - c.win_date <
                datetime.timedelta(seconds=1))
        self.assertTrue(c.winner.id in [user1.id, user2.id, user3.id])

