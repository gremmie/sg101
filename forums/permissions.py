"""
This module does permissions checking for the forums application.

"""
from django.core.cache import cache

# How long (in secs) to cache group information for various entities:
CATEGORY_TIMEOUT = 4 * 60 * 60
FORUM_TIMEOUT = 4 * 60 * 60
USER_TIMEOUT = 15 * 60


def can_access(category, user):
    """
    This function returns True if the given user can access the forum category
    and False otherwise.

    """
    if user.is_superuser:
        return True

    # If this category has no groups assigned to it, return True. Else, return
    # True if the user belongs to a group that has been assigned to this
    # category, and False otherwise.

    # Get the groups assigned to this category.
    cat_groups = get_category_groups(category)

    if len(cat_groups) == 0:
        return True         # No groups => public category

    user_groups = get_user_groups(user)
    return bool(user_groups & cat_groups)


def can_moderate(forum, user):
    """
    Returns True if the user can moderate the forum.

    """
    # Get the simple cases out of the way first:
    if not user.is_authenticated():
        return False
    elif user.is_superuser:
        return True

    # If we get here, we have to see if there is an intersection between the
    # user's groups and the forum's moderator groups.

    forum_groups = get_forum_groups(forum)
    user_groups = get_user_groups(user)

    return bool(user_groups & forum_groups)


def can_post(topic, user):
    """
    Returns True if the user can post in the topic and False otherwise.

    """
    if not user.is_authenticated():
        return False
    if user.is_superuser or can_moderate(topic.forum, user):
        return True

    return not topic.locked and can_access(topic.forum.category, user)


def get_user_groups(user):
    """
    Returns a set of group ID's that the user belongs to.

    """
    user_groups_key = '%s_groups' % user.username
    return _get_groups(user_groups_key, user.groups.all(), USER_TIMEOUT)


def get_forum_groups(forum):
    """
    Returns a set of group ID's of the forum's moderator groups.

    """
    forum_groups_key = 'forum_%d_mods' % forum.id
    return _get_groups(forum_groups_key, forum.moderators.all(), FORUM_TIMEOUT)


def get_category_groups(category):
    """
    Returns a set of group ID's of the groups that can access this forum
    category.

    """
    cat_groups_key = 'cat_%d_groups' % category.id
    return _get_groups(cat_groups_key, category.groups.all(), CATEGORY_TIMEOUT)


def _get_groups(key, qs, timeout):
    """
    This internal function contains the code common to the get_xxx_groups()
    functions. Returns a set of group ID's from the cache. If the set is not
    found in the cache, the set is generated from the queryset qs and cached
    with the given timeout.

    key - the cache key for the set of group ID's
    qs - the query set of groups to query if the set is not in the cache
    timeout - the cache timeout to use

    """
    groups = cache.get(key)
    if groups is None:
        groups = set([g.id for g in qs])
        cache.set(key, groups, timeout)

    return groups
