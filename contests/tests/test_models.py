"""
Model tests for the contests application.

"""
import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from contests.models import Contest


class ContestTestCase(TestCase):

    def test_creation_date(self):

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=False,
                end_date=timezone.now() + datetime.timedelta(days=30))

        c.save()

        self.assertTrue(c.creation_date)
        self.assertTrue(timezone.now() - c.creation_date <
                datetime.timedelta(seconds=1))

    def test_is_active(self):

        now = timezone.now()
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

        now = timezone.now()
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
                win_date=now)
        c.save()
        c.contestants.add(user)
        c.winners.add(user)

        self.assertFalse(c.can_enter())

        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        c = Contest(title='test 2',
                slug='test-2',
                description='test 2',
                is_public=True,
                creation_date=start,
                end_date=end,
                win_date=end + datetime.timedelta(days=1))
        c.save()
        c.contestants.add(user)
        c.winners.add(user)

        self.assertFalse(c.can_enter())

    def test_pick_winners(self):

        now = timezone.now()
        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=False,
                creation_date=start,
                end_date=end,
                num_winners=1)
        c.save()

        user1 = User.objects.create_user('test_user1', '', 'password')
        user1.save()
        user2 = User.objects.create_user('test_user2', '', 'password')
        user2.save()
        user3 = User.objects.create_user('test_user3', '', 'password')
        user3.save()

        c.contestants.add(user1, user2, user3)

        c.pick_winners()

        self.assertTrue(timezone.now() - c.win_date <
                datetime.timedelta(seconds=1))

        winners = list(c.winners.all())
        self.assertEqual(len(winners), 1)
        self.assertTrue(winners[0].id in [user1.id, user2.id, user3.id])

    def test_pick_winners2(self):

        now = timezone.now()
        start = now - datetime.timedelta(days=7)
        end = start - datetime.timedelta(days=3)

        c = Contest(title='test',
                slug='test',
                description='test',
                is_public=False,
                creation_date=start,
                end_date=end,
                num_winners=2)
        c.save()

        user1 = User.objects.create_user('test_user1', '', 'password')
        user1.save()
        user2 = User.objects.create_user('test_user2', '', 'password')
        user2.save()
        user3 = User.objects.create_user('test_user3', '', 'password')
        user3.save()

        c.contestants.add(user1, user2, user3)

        c.pick_winners()

        self.assertTrue(timezone.now() - c.win_date <
                datetime.timedelta(seconds=1))

        winners = list(c.winners.all())
        self.assertEqual(len(winners), 2)

        user_ids = set([user1.id, user2.id, user3.id])
        self.assertTrue(winners[0].id in user_ids)
        self.assertTrue(winners[1].id in user_ids)
        self.assertTrue(winners[0].id != winners[1].id)

