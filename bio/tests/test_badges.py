"""
Unit tests for the bio application badge utilities.

"""
from django.test import TestCase
from django.contrib.auth.models import User

from bio.badges import award_badge, NEWS_PIN
from bio.models import Badge, BadgeOwnership


class AwardBadgeTestCase(TestCase):
    fixtures = ['badges.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')

    def test_unknown_badge(self):
        award_badge(4096, self.user)
        self.assertEqual(BadgeOwnership.objects.count(), 0)

    def test_user_has_the_badge(self):
        badge = Badge.objects.get(numeric_id=NEWS_PIN)
        bo = BadgeOwnership(profile=self.user.profile, badge=badge, count=7)
        bo.save()

        award_badge(badge.numeric_id, self.user)
        bo = BadgeOwnership.objects.get(profile=self.user.profile, badge=badge)
        self.assertEqual(bo.count, 8)

    def test_user_does_not_have_the_badge(self):
        badge = Badge.objects.get(numeric_id=NEWS_PIN)
        award_badge(badge.numeric_id, self.user)
        bo = BadgeOwnership.objects.get(profile=self.user.profile, badge=badge)
        self.assertEqual(bo.count, 1)
