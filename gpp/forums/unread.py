"""
This file contains routines for implementing the "has unread" feature. 
Forums, topics, and posts are displayed with a visual indication if they have
been read or not.
"""
import datetime

from forums.models import ForumLastVisit, TopicLastVisit, Topic


THRESHOLD = datetime.timedelta(days=7)

#######################################################################

def get_forum_unread_status(qs, user):
    if not user.is_authenticated():
        for forum in qs:
            forum.has_unread = False
        return

    now = datetime.datetime.now()
    min_date = now - THRESHOLD

    # retrieve ForumLastVisit records in one SQL query
    forum_ids = [forum.id for forum in qs]
    flvs = ForumLastVisit.objects.filter(user=user, 
            forum__in=forum_ids).select_related()
    flvs = dict([(flv.forum.id, flv) for flv in flvs])

    for forum in qs:
        # Edge case: forum has no posts
        if forum.last_post is None:
            forum.has_unread = False
            continue

        # Get the ForumLastVisit record
        if forum.id in flvs:
            flv = flvs[forum.id]
        else:
            # One doesn't exist, create a default one for next time,
            # mark it as having no unread topics, and bail.
            flv = ForumLastVisit(user=user, forum=forum)
            flv.begin_date = now
            flv.end_date = now
            flv.save()
            forum.has_unread = False
            continue

        # If the last visit record was too far in the past,
        # catch that user up and mark as no unreads.
        if now - flv.end_date > THRESHOLD:
            forum.catchup(user, flv)
            forum.has_unread = False
            continue

        # Check the easy cases first. Check the last_post in the
        # forum. If created after the end_date in our window, there
        # are new posts. Likewise, if before the begin_date in our window,
        # there are no new posts.
        if forum.last_post.creation_date > flv.end_date:
            forum.has_unread = True
        elif forum.last_post.creation_date < flv.begin_date:
            if not flv.is_caught_up():
                forum.catchup(user, flv)
            forum.has_unread = False
        else:
            # Going to have to examine the topics in our window.
            # First adjust our window if it is too old.
            if now - flv.begin_date > THRESHOLD:
                flv.begin_date = min_date
                flv.save()
                TopicLastVisit.objects.filter(user=user, topic__forum=forum,
                        last_visit__lt=min_date).delete()

            topics = Topic.objects.filter(forum=forum, 
                    creation_date__gt=flv.begin_date)
            tracked_topics = TopicLastVisit.objects.filter(user=user,
                    topic__forum=forum, last_visit__gt=flv.begin_date)

            # If the number of topics created since our window was started 
            # is greater than the tracked topic records, then there are new
            # posts.
            if topics.count() > tracked_topics.count():
                forum.has_unread = True
                continue

            tracked_dict = dict([(t.id, t) for t in tracked_topics])

            for topic in topics:
                if topic.id in tracked_dict:
                    if topic.update_date > tracked_dict[topic.id].last_visit:
                        forum.has_unread = True
                        continue
                else:
                    forum.has_unread = True
                    continue

            # If we made it through the above loop without continuing, then
            # we are all caught up.
            forum.catchup(user, flv)
            forum.has_unread = False

#######################################################################

def get_topic_unread_status(forum, topics, user):

    # Edge case: no topics 
    if forum.last_post is None:
        return

    # This service isn't provided to unauthenticated users
    if not user.is_authenticated():
        for topic in topics:
            topic.has_unread = False
        return

    now = datetime.datetime.now()

    # Get the ForumLastVisit record
    try:
        flv = ForumLastVisit.objects.get(forum=forum, user=user)
    except ForumLastVisit.DoesNotExist:
        # One doesn't exist, create a default one for next time,
        # mark it as having no unread topics, and bail.
        flv = ForumLastVisit(user=user, forum=forum)
        flv.begin_date = now
        flv.end_date = now
        flv.save()
        for topic in topics:
            topic.has_unread = False
        return

    # Are all the posts before our window? If so, all have been read.
    if forum.last_post.creation_date < flv.begin_date:
        for topic in topics:
            topic.has_unread = False
        return

    topic_ids = [topic.id for topic in topics]
    tlvs = TopicLastVisit.objects.filter(user=user, topic__id__in=topic_ids)
    tlvs = dict([(tlv.topic.id, tlv) for tlv in tlvs])

    # Otherwise we have to go through the topics one by one:
    for topic in topics:
        if topic.update_date < flv.begin_date:
            topic.has_unread = False
        elif topic.update_date > flv.end_date:
            topic.has_unread = True
        elif topic.id in tlvs:
            topic.has_unread = topic.update_date > tlvs[topic.id].last_visit
        else:
            topic.has_unread = True

#######################################################################

def get_post_unread_status(topic, posts, user):
    # This service isn't provided to unauthenticated users
    if not user.is_authenticated():
        for post in posts:
            post.unread = False
        return

    # Get the ForumLastVisit record
    try:
        flv = ForumLastVisit.objects.get(forum=topic.forum, user=user)
    except ForumLastVisit.DoesNotExist:
        # One doesn't exist, all posts are old.
        for post in posts:
            post.unread = False
        return

    # Are all the posts before our window? If so, all have been read.
    if topic.last_post.creation_date < flv.begin_date:
        for post in posts:
            post.unread = False
        return

    # Do we have a topic last visit record for this topic?

    try:
        tlv = TopicLastVisit.objects.get(user=user, topic=topic)
    except TopicLastVisit.DoesNotExist:
        # No we don't, we could be all caught up, or all are new
        for post in posts:
            post.unread = post.creation_date > flv.end_date
    else:
        for post in posts:
            post.unread = post.creation_date > tlv.last_visit
