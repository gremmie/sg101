"""Antispam utility functions other apps can use."""
import datetime
import logging
import textwrap

from django.core.cache import cache

from antispam import SPAM_PHRASE_KEY
from antispam.models import SpamPhrase
from core.functions import email_admins
from bio.models import STA_SUSPENDED, STA_SPAMMER
from comments.models import Comment
from forums.tools import delete_user_posts


def contains_spam(s):
    """This function returns True if the supplied string s contains any spam
    phrases and False otherwise.
    """
    phrases = _get_spam_phrases()
    s = s.lower()
    for spam in phrases:
        if spam in s:
            return True

    return False


def spam_check(request, content):
    """This function checks the supplied content for spam if the user from the
    supplied request is a stranger (new to the site). If spam is found, the
    function makes a log entry, emails the admins, suspends the user's account
    and returns True. If spam is not found, False is returned.
    It is assumed that request.user is an authenticated user and thus has a
    user profile.
    """
    user = request.user
    if user.get_profile().is_stranger() and contains_spam(content):

        ip = request.META.get('REMOTE_ADDR', "unknown")

        msg = textwrap.dedent("""\
            SPAM FILTER TRIPPED by %s
            PATH: %s
            IP: %s
            Message:
            %s
            """ % (user.username, request.path, ip, content))

        logging.info(msg)
        email_admins("SPAM FILTER TRIPPED BY %s" % user.username, msg)
        suspend_user(user)
        return True

    return False


def suspend_user(user):
    """This function marks the user as suspended."""
    user.is_active = False
    user.save()
    profile = user.get_profile()
    profile.status = STA_SUSPENDED
    profile.status_date = datetime.datetime.now()
    profile.save(content_update=False)
    logging.info("User suspended: %s", user.username)


def deactivate_spammer(user):
    """
    This function deactivate's the user, marks them as a spammer, then
    deletes the user's comments and forum posts. The spammer's profile is
    cleared so any spam links won't show up anymore.

    """
    user.is_active = False
    user.save()

    profile = user.get_profile()
    profile.status = STA_SPAMMER
    profile.status_date = datetime.datetime.now()
    profile.reset_text_fields()
    if profile.avatar:
        profile.avatar.delete(save=False)
    profile.save()

    Comment.objects.filter(user=user).delete()
    delete_user_posts(user)

    logging.info("User deactivated for spam: %s", user.username)


def _get_spam_phrases():
    """
    This function returns the current list of spam phrase strings.
    The strings are cached to avoid hitting the database.

    """
    phrases = cache.get(SPAM_PHRASE_KEY)
    if phrases:
        return phrases

    phrases = SpamPhrase.objects.values_list('phrase', flat=True)
    cache.set(SPAM_PHRASE_KEY, phrases)
    return phrases
