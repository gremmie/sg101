"""This module contains user profile badge-related functionality."""

from bio.models import Badge
from bio.models import BadgeOwnership


# Numeric ID's for badges that are awarded for user actions:
(CONTRIBUTOR_PIN, CALENDAR_PIN, NEWS_PIN, LINK_PIN, DOWNLOAD_PIN,
        SECURITY_PIN) = range(6)


def award_badge(badge_id, user):
    """This function awards the badge specified by badge_id
    to the given user. If the user already has the badge,
    the badge count is incremented by one.
    """
    import logging
    try:
        badge = Badge.objects.get(numeric_id=badge_id)
    except Badge.DoesNotExist:
        logging.error("Can't award badge with numeric_id = %d" % badge_id)
        return

    profile = user.get_profile()

    # Does the user already have badges of this type?
    try:
        bo = BadgeOwnership.objects.get(profile=profile, badge=badge)
    except BadgeOwnership.DoesNotExist:
        # No badge of this type, yet
        bo = BadgeOwnership(profile=profile, badge=badge, count=1)
    else:
        # Already have this badge
        bo.count += 1
    bo.save()
