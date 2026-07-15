"""Tests for the bio app's signal handlers."""

from collections import namedtuple

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase

import bio.badges
from bio.models import Badge
from bio.models import BadgeOwnership
from bio.models import UserProfile
from donations.models import Donation
from downloads.models import Download
import downloads.receivers
from news.models import Story
from potd.models import Photo
import potd.receivers
from weblinks.models import Link
import weblinks.receivers


FakeDonation = namedtuple('FakeDonation', ['is_anonymous', 'user'])
FakeUserObject = namedtuple('FakeUserObject', ['user'])
FakeStory = namedtuple('FakeStory', ['submitter'])


class ReceiverTestCase(TestCase):

    fixtures = ['badges.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')

        # Don't let these signal handlers fire either
        post_save.disconnect(sender=Link, dispatch_uid='weblinks.receivers')
        post_save.disconnect(sender=Download, dispatch_uid='downloads.receivers')
        post_save.disconnect(sender=Photo, dispatch_uid='potd.receivers')

    def tearDown(self):
        post_save.connect(weblinks.receivers.on_link_save, sender=Link,
                          dispatch_uid='weblinks.receivers')
        post_save.connect(downloads.receivers.on_download_save, sender=Download,
                          dispatch_uid='downloads.receivers')
        post_save.connect(potd.receivers.on_photo_save, sender=Photo,
                          dispatch_uid='potd.receivers')

    def test_profile_creation(self):
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(self.user.profile, profile)

    def test_donation_created(self):
        donation = FakeDonation(False, self.user)
        post_save.send(sender=Donation, created=True, instance=donation)

        badge = Badge.objects.get(numeric_id=bio.badges.CONTRIBUTOR_PIN)
        ownership = BadgeOwnership.objects.get(badge=badge, profile=self.user.profile)
        self.assertEqual(ownership.count, 1)

    def test_donation_updated(self):
        donation = FakeDonation(False, self.user)
        post_save.send(sender=Donation, created=False, instance=donation)

        badge = Badge.objects.get(numeric_id=bio.badges.CONTRIBUTOR_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)

    def test_donation_anonymous(self):
        donation = FakeDonation(True, self.user)
        post_save.send(sender=Donation, created=False, instance=donation)

        badge = Badge.objects.get(numeric_id=bio.badges.CONTRIBUTOR_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)

    def test_donation_no_user(self):
        donation = FakeDonation(False, None)
        post_save.send(sender=Donation, created=False, instance=donation)

        badge = Badge.objects.get(numeric_id=bio.badges.CONTRIBUTOR_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)

    def test_donation_anon_and_no_user(self):
        donation = FakeDonation(True, None)
        post_save.send(sender=Donation, created=False, instance=donation)

        badge = Badge.objects.get(numeric_id=bio.badges.CONTRIBUTOR_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)

    def test_link_created(self):
        link = FakeUserObject(self.user)
        post_save.send(sender=Link, created=True, instance=link)

        badge = Badge.objects.get(numeric_id=bio.badges.LINK_PIN)
        ownership = BadgeOwnership.objects.get(badge=badge, profile=self.user.profile)
        self.assertEqual(ownership.count, 1)

    def test_link_updated(self):
        link = FakeUserObject(self.user)
        post_save.send(sender=Link, created=False, instance=link)

        badge = Badge.objects.get(numeric_id=bio.badges.LINK_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)

    def test_download_created(self):
        dl = FakeUserObject(self.user)
        post_save.send(sender=Download, created=True, instance=dl)

        badge = Badge.objects.get(numeric_id=bio.badges.DOWNLOAD_PIN)
        ownership = BadgeOwnership.objects.get(badge=badge, profile=self.user.profile)
        self.assertEqual(ownership.count, 1)

    def test_download_updated(self):
        dl = FakeUserObject(self.user)
        post_save.send(sender=Download, created=False, instance=dl)

        badge = Badge.objects.get(numeric_id=bio.badges.DOWNLOAD_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)

    def test_story_created(self):
        story = FakeStory(self.user)
        post_save.send(sender=Story, created=True, instance=story)

        badge = Badge.objects.get(numeric_id=bio.badges.NEWS_PIN)
        ownership = BadgeOwnership.objects.get(badge=badge, profile=self.user.profile)
        self.assertEqual(ownership.count, 1)

    def test_story_updated(self):
        story = FakeStory(self.user)
        post_save.send(sender=Story, created=False, instance=story)

        badge = Badge.objects.get(numeric_id=bio.badges.NEWS_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)

    def test_photo_created(self):
        photo = FakeUserObject(self.user)
        post_save.send(sender=Photo, created=True, instance=photo)

        badge = Badge.objects.get(numeric_id=bio.badges.POTD_PIN)
        ownership = BadgeOwnership.objects.get(badge=badge, profile=self.user.profile)
        self.assertEqual(ownership.count, 1)

    def test_photo_updated(self):
        photo = FakeUserObject(self.user)
        post_save.send(sender=Photo, created=False, instance=photo)

        badge = Badge.objects.get(numeric_id=bio.badges.POTD_PIN)
        self.assertRaises(BadgeOwnership.DoesNotExist,
                          BadgeOwnership.objects.get,
                          badge=badge, profile=self.user.profile)
