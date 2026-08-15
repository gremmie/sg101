"""
Tests for the antispam application.

"""
import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils import timezone

from unittest.mock import call, patch, Mock

from antispam import SPAM_PHRASE_KEY
from antispam.models import SpamPhrase
from antispam.utils import contains_spam, deactivate_spammer, spam_check
from comments.models import Comment
from polls.models import Poll
from elsewhere.models import WebsiteProfile
from shoutbox.models import Shout
from bio.models import STA_ACTIVE, STA_SPAMMER, STA_STRANGER, STA_SUSPENDED


class AntispamUtilsCase(TestCase):

    def test_no_phrases(self):
        """
        Tests that an empty spam phrase table works.

        """
        cache.delete(SPAM_PHRASE_KEY)
        self.assertFalse(contains_spam("Here is some random text."))

    def test_phrases(self):
        """
        Simple test of some phrases.

        """
        SpamPhrase.objects.create(phrase="grytner")
        SpamPhrase.objects.create(phrase="allday.ru")
        SpamPhrase.objects.create(phrase="stefa.pl")

        self.assertTrue(contains_spam("grytner"))
        self.assertTrue(contains_spam("11grytner"))
        self.assertTrue(contains_spam("11grytner>"))
        self.assertTrue(contains_spam("1djkl jsd stefa.pl"))
        self.assertTrue(contains_spam("1djkl jsd <stefa.pl---sd8"))
        self.assertTrue(contains_spam("1dsdjallday.rukl jsd <stefa.pl---sd8"))
        self.assertTrue(contains_spam(" 1djallday.rukl"))
        self.assertFalse(contains_spam("this one is spam free."))

    def test_deactivate_spammer(self):
        """
        Test the deactivate_spammer() function.

        """
        user = User.objects.create_user('spammer_guy', '', 'password')
        user.save()

        profile = user.profile
        profile.location = 'Spamville'
        profile.country = 'US'
        profile.birthday = datetime.date.today()
        profile.occupation = 'Spammer'
        profile.interests = 'Spamming websites'
        profile.profile_text = 'I spam a lot.'
        profile.signature = 'I spammed you!'
        profile.save()

        now=timezone.now()

        # create a poll item to comment on
        poll = Poll(start_date=now,
                end_date=now,
                is_enabled=True,
                question='?')
        poll.save()

        comment = Comment(
            content_type=ContentType.objects.get_for_model(poll),
            object_id=poll.pk,
            user=user,
            comment='Spam Spam Spam',
            ip_address='127.0.0.1',
            is_public=True,
            is_removed=False)
        comment.save()

        website = WebsiteProfile(user=user, name='spam', url='spam')
        website.save()

        shout = Shout(user=user, shout_date=now, shout='spam')
        shout.save()

        deactivate_spammer(user)

        profile = user.profile
        self.assertFalse(profile.location)
        self.assertFalse(profile.country)
        self.assertIsNone(profile.birthday)
        self.assertFalse(profile.occupation)
        self.assertFalse(profile.interests)
        self.assertFalse(profile.profile_text)
        self.assertFalse(profile.profile_html)
        self.assertFalse(profile.signature)
        self.assertFalse(profile.signature_html)
        self.assertEqual(profile.status, STA_SPAMMER)

        # Both sides UTC: status_date is aware now, and date.today() would be
        # the container's local date, which only agrees by coincidence.
        self.assertEqual(profile.status_date.date(), timezone.now().date())

        self.assertEqual(Comment.objects.filter(user=user).count(), 0)
        self.assertEqual(WebsiteProfile.objects.filter(user=user).count(), 0)
        self.assertEqual(Shout.objects.filter(user=user).count(), 0)


class AntispamSpamCheckTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user('spammer_guy', '', 'password')
        user.save()
        SpamPhrase.objects.create(phrase="grytner")

    @patch('antispam.utils.email_admins')
    def test_not_a_stranger(self, email_admins_mock):
        user = User.objects.get(username='spammer_guy')
        user.profile.status = STA_ACTIVE
        user.profile.save(content_update=False)

        request = Mock()
        request.user = user
        result = spam_check(request, 'grytner')

        self.assertFalse(result)
        user = User.objects.get(username='spammer_guy')
        self.assertTrue(user.is_active)
        self.assertEqual(user.profile.status, STA_ACTIVE)
        self.assertEqual(email_admins_mock.mock_calls, [])

    @patch('antispam.utils.email_admins')
    def test_stranger_no_spam(self, email_admins_mock):
        user = User.objects.get(username='spammer_guy')
        user.profile.status = STA_ACTIVE
        user.profile.save(content_update=False)

        request = Mock()
        request.user = user
        result = spam_check(request, 'not spam')

        self.assertFalse(result)
        user = User.objects.get(username='spammer_guy')
        self.assertTrue(user.is_active)
        self.assertEqual(user.profile.status, STA_ACTIVE)
        self.assertEqual(email_admins_mock.mock_calls, [])

    @patch('antispam.utils.email_admins')
    def test_stranger_with_spam(self, email_admins_mock):
        user = User.objects.get(username='spammer_guy')
        user.profile.status = STA_STRANGER
        user.profile.save(content_update=False)

        request = Mock()
        request.user = user
        request.path = '/some/path'
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        result = spam_check(request, 'grytner')

        self.assertTrue(result)
        user = User.objects.get(username='spammer_guy')
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.status, STA_SUSPENDED)

        expected_msg = ('SPAM FILTER TRIPPED by spammer_guy\n'
                        'PATH: /some/path\n'
                        'IP: 127.0.0.1\n'
                        'Message:\n'
                        'grytner\n')
        self.assertEqual(email_admins_mock.mock_calls, [
            call('SPAM FILTER TRIPPED BY spammer_guy', expected_msg),
        ])
