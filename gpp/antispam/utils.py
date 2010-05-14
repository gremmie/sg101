"""Antispam utility functions other apps can use."""
from django.core.cache import cache

from antispam import SPAM_PHRASE_KEY
from antispam.models import SpamPhrase


def contains_spam(s):
    """This function returns True if the supplied string s contains any spam
    phrases and False otherwise.
    """
    phrases = _get_spam_phrases()
    for spam in phrases:
        if spam in s:
            return True

    return False


def _get_spam_phrases():
    """This function returns the current list of spam phrase strings.
    The strings are cached to avoid hitting the database.
    """
    phrases = cache.get(SPAM_PHRASE_KEY)
    if phrases:
        return phrases

    phrases = SpamPhrase.objects.values_list('phrase', flat=True)
    cache.set(SPAM_PHRASE_KEY, phrases)
    return phrases

