"""
Tests for the antispam application.
"""
from django.test import TestCase
from django.core.cache import cache

from antispam import SPAM_PHRASE_KEY
from antispam.models import SpamPhrase
from antispam.utils import contains_spam


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

