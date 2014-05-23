"""
Tests for the antispam application.

"""
import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache

from antispam import SPAM_PHRASE_KEY
from antispam.models import SpamPhrase
from antispam.utils import contains_spam, deactivate_spammer

from comments.models import Comment
from polls.models import Poll
from elsewhere.models import WebsiteProfile
from shoutbox.models import Shout
from bio.models import STA_SPAMMER


class AntispamCase(TestCase):

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

        self.assert_(contains_spam("grytner"))
        self.assert_(contains_spam("11grytner"))
        self.assert_(contains_spam("11grytner>"))
        self.assert_(contains_spam("1djkl jsd stefa.pl"))
        self.assert_(contains_spam("1djkl jsd <stefa.pl---sd8"))
        self.assert_(contains_spam("1dsdjallday.rukl jsd <stefa.pl---sd8"))
        self.assert_(contains_spam(" 1djallday.rukl"))
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

        now=datetime.datetime.now()

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

        status_date = datetime.date(year=profile.status_date.year,
                month=profile.status_date.month,
                day=profile.status_date.day)
        self.assertEqual(status_date, datetime.date.today())

        self.assertEqual(Comment.objects.filter(user=user).count(), 0)
        self.assertEqual(WebsiteProfile.objects.filter(user=user).count(), 0)
        self.assertEqual(Shout.objects.filter(user=user).count(), 0)
