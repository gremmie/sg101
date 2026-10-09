"""
This module maintains the latest posts datastore. The latest posts are often
needed by RSS feeds, "latest posts" template tags, etc. This module listens for
the post_content_update signal, then bundles the post up and stores it by forum
ID in Redis. We also maintain a combined forums list. This allows quick
retrieval of the latest posts and avoids some slow SQL queries.

We also do things like send topic notification emails, auto-favorite, and
auto-subscribe functions here rather than bog the user down in the request /
response cycle.

"""
# Maintenance notes:
# How we use Redis in this module:
# 
# Forum post processing:
#
# * Forum posts are turned into Python dictionaries, then converted to JSON and
#   stored under keys: forums:post:id
# * Each forum has a list in Redis stored under the key: forums:rss:id. This
#   is a list of post IDs.
# * There is also a key called forums:rss:* which is the combined latest
#   feed. It is also a list of post IDs.
# * A sorted set is maintained that keeps track of the reference count for each
#   post. When a new post is created, this reference count is 2 because it is
#   stored in both the combined list and the parent forum list.
#   This sorted set is stored under the key: forums:post_ref_cnt.
# * When a post falls off a list due to aging, the reference count in the
#   ordered set is decremented. If it falls to zero, the post's key is deleted
#   from Redis.
# * When a post is edited, and it is in Redis, we simply update the JSON
#   content.
# * When a post is deleted, and it is in Redis, it is removed from the 2 lists, 
#   the ordered set, and deleted from Redis.
# * When the RSS feed wants to update, it simply pulls down the entire list of
#   post IDs for the feed of interest, then does a get on all the posts.
#
# Topics with recent posts processing:
#
# * A key is created for each topic that is updated.
# * An ordered set of topics is maintained with the current time as the score.
# * An updated topic gets its score bumped.
# * We only allow MAX_UPDATED_TOPICS number of topics in the set. We sort the
#   set by score, and the expired topics are removed from the set and their keys
#   are deleted from Redis.
# * The template tag (or anyone) who wants the list of topics with new posts
#   gets the list of IDs sorted by score from newest to oldest. An mget is then
#   performed to get all the topic data and it is deserialized from JSON.
#
# We also maintain topic and post counts in Redis since select(*) can take a
# while with MySQL InnoDb.
#
import datetime
import json
import logging

import dateutil.parser
from django.dispatch import receiver
from django.template.loader import render_to_string
import redis

from forums.signals import post_content_update, topic_content_update
from forums.models import Forum, Topic, Post, Attachment
from forums.views.subscriptions import notify_topic_subscribers
from forums.tools import auto_favorite, auto_subscribe
from core.services import get_redis_connection
from core.markup import site_markup

# This constant controls how many latest posts per forum we store
MAX_POSTS = 50

# This controls how many updated topics we track
MAX_UPDATED_TOPICS = 50

# Redis key names:
POST_COUNT_KEY = "forums:public_post_count"
TOPIC_COUNT_KEY = "forums:public_topic_count"
UPDATED_TOPICS_SET_KEY = "forums:updated_topics:set"
UPDATED_TOPIC_KEY = "forums:updated_topics:%s"
POST_KEY = "forums:post:%s"
FORUM_RSS_KEY = "forums:rss:%s"
ALL_FORUMS_RSS_KEY = "forums:rss:*"
POST_SET_KEY = "forums:post_ref_cnt"

logger = logging.getLogger(__name__)


@receiver(post_content_update, dispatch_uid='forums.latest_posts')
def on_post_update(sender, **kwargs):
    """
    This function is our signal handler, called when a post has been updated
    or created.

    We kick off a Celery task to perform work outside of the request/response
    cycle.

    """
    if kwargs['created']:
        forums.tasks.new_post_task.delay(sender.id)
    else:
        forums.tasks.updated_post_task.delay(sender.id)


def process_new_post(post_id):
    """
    This function is run on a Celery task. It performs all new-post processing.

    """
    try:
        post = Post.objects.select_related().get(pk=post_id)
    except Post.DoesNotExist:
        logger.warning("process_new_post: post %d does not exist", post_id)
        return

    # selectively process posts from non-public forums
    public_forums = Forum.objects.public_forum_ids()

    if post.topic.forum.id in public_forums:
        conn = get_redis_connection()
        _update_post_feeds(conn, post)
        _update_post_count(conn, public_forums)
        _update_latest_topics(conn, post)

    # send out any email notifications
    notify_topic_subscribers(post, defer=False)

    # perform any auto-favorite and auto-subscribe actions for the new post
    auto_favorite(post)
    auto_subscribe(post)


def process_updated_post(post_id):
    """
    This function is run on a Celery task. It performs all updated-post
    processing.

    """
    # Is this post ID in a RSS feed?
    conn = get_redis_connection()
    post_key = POST_KEY % post_id
    post_val = conn.get(post_key)

    if post_val is not None:
        # Update the post value in Redis
        try:
            post = Post.objects.select_related().get(pk=post_id)
        except Post.DoesNotExist:
            logger.warning("process_updated_post: post %d does not exist", post_id)
            return
        conn.set(post_key, _serialize_post(post))


def _update_post_feeds(conn, post):
    """
    Updates the forum feeds we keep in Redis so that our RSS feeds are quick.

    """
    post_key = POST_KEY % post.id
    post_value = _serialize_post(post)

    pipeline = conn.pipeline()

    # Store serialized post content under its own key
    pipeline.set(post_key, post_value)

    # Store in the RSS feed for the post's forum
    forum_key = FORUM_RSS_KEY % post.topic.forum.id
    pipeline.lpush(forum_key, post.id)

    # Store in the RSS feed for combined forums
    pipeline.lpush(ALL_FORUMS_RSS_KEY, post.id)

    # Store reference count for the post
    pipeline.zadd(POST_SET_KEY, {post.id: 2})

    results = pipeline.execute()

    # Make sure our forums RSS lists lengths are not exceeded

    if results[1] > MAX_POSTS or results[2] > MAX_POSTS:
        pipeline = conn.pipeline()

        # Truncate lists of posts:
        if results[1] > MAX_POSTS:
            pipeline.rpop(forum_key)
        if results[2] > MAX_POSTS:
            pipeline.rpop(ALL_FORUMS_RSS_KEY)
        post_ids = pipeline.execute()

        # Decrement reference count(s)
        pipeline = conn.pipeline()
        for post_id in post_ids:
            pipeline.zincrby(POST_SET_KEY, -1, post_id)
        scores = pipeline.execute()

        # If any reference counts have fallen to 0, clean up:
        if not all(scores):
            pipeline = conn.pipeline()

            # remove from post set
            ids = [post_ids[n] for n, s in enumerate(scores) if s <= 0.0]
            pipeline.zrem(POST_SET_KEY, *ids)

            # remove serialized post data
            keys = [POST_KEY % n for n in ids]
            pipeline.delete(*keys)

            pipeline.execute()


def _update_post_count(conn, public_forums):
    """
    Updates the post count we cache in Redis. Doing a COUNT(*) on the post table
    can be expensive in MySQL InnoDB.

    """
    result = conn.incr(POST_COUNT_KEY)
    if result == 1:
        # it is likely redis got trashed, so re-compute the correct value

        count = Post.objects.filter(topic__forum__in=public_forums).count()
        conn.set(POST_COUNT_KEY, count)


def _update_latest_topics(conn, post):
    """
    Updates the "latest topics with new posts" list we cache in Redis for speed.
    There is a template tag and forum view that uses this information.

    """
    topic_id = post.topic.id
    topic_content = _topic_content(post)
    topic_score = topic_content['date']
    topic_json = json.dumps(topic_content)
    key = UPDATED_TOPIC_KEY % topic_id

    pipeline = conn.pipeline()
    pipeline.set(key, topic_json)
    pipeline.zadd(UPDATED_TOPICS_SET_KEY, {topic_id: topic_score})
    pipeline.zcard(UPDATED_TOPICS_SET_KEY)
    results = pipeline.execute()

    # delete topics beyond our maximum count
    num_topics = results[-1]
    num_to_del = num_topics - MAX_UPDATED_TOPICS
    if num_to_del > 0:
        # get the IDs of the topics we need to delete first
        start = 0
        stop = num_to_del - 1   # Redis indices are inclusive
        old_ids = conn.zrange(UPDATED_TOPICS_SET_KEY, start, stop)

        keys = [UPDATED_TOPIC_KEY % n for n in old_ids]
        conn.delete(*keys)

        # now delete the oldest num_to_del topics
        conn.zremrangebyrank(UPDATED_TOPICS_SET_KEY, start, stop)


def _topic_content(post):
    """The updated-topic entry for a topic whose newest post is `post`."""
    # timestamp(), not time.mktime(timetuple()): timetuple() discards the
    # offset and mktime() reads the remainder as container-local time, so the
    # score was only ever right when the container's clock happened to agree
    # with TIME_ZONE. _deserialize_topic_date() is the other half of this.
    return {
        'title': post.topic.name,
        'author': post.user.username,
        'date': int(post.creation_date.timestamp()),
        'url': post.topic.get_latest_post_url()
    }


def rebuild(conn):
    """
    Replaces everything this module keeps in Redis with what the database says
    it should be: the feeds, the posts they hold, the updated topics and the
    counts. For use after a database restore, which leaves Redis describing the
    old database under IDs the restored one reuses.

    The feeds and topics are replayed oldest first through the same functions
    that maintain them on a live site, so they come out exactly as live
    processing would have left them.

    """
    public_forums = _public_forum_ids()

    keys = list(conn.scan_iter('forums:*'))
    if keys:
        conn.delete(*keys)

    feeds = _expected_feeds(public_forums)
    post_ids = set().union(*feeds.values())
    posts = Post.objects.filter(id__in=post_ids).select_related(
            'topic', 'topic__forum', 'user').order_by('creation_date', 'id')
    for post in posts:
        _update_post_feeds(conn, post)

    for post in reversed(_expected_topic_posts(public_forums)):
        _update_latest_topics(conn, post)

    post_count, topic_count = _expected_counts(public_forums)
    conn.set(POST_COUNT_KEY, post_count)
    conn.set(TOPIC_COUNT_KEY, topic_count)


def verify(conn):
    """
    Compares what this module keeps in Redis with the database, and returns a
    list of the differences found, as messages. An empty list means they agree.
    Nothing is written.

    """
    public_forums = _public_forum_ids()
    problems = []

    # The feeds: exactly the expected lists, and no others.
    feeds = _expected_feeds(public_forums)
    held_keys = {key for key in conn.scan_iter(FORUM_RSS_KEY % '*')}
    held_keys.add(ALL_FORUMS_RSS_KEY)
    for key in sorted(held_keys | set(feeds)):
        expected = feeds.get(key, [])
        actual = [int(n) for n in conn.lrange(key, 0, -1)]
        if actual != expected:
            problems.append(_describe_list(key, actual, expected))

    # The posts the feeds hold: present, current, and counted once per list.
    references = {}
    for ids in feeds.values():
        for post_id in ids:
            references[post_id] = references.get(post_id, 0) + 1

    cached_ids = {int(key.rsplit(':', 1)[1])
                  for key in conn.scan_iter(POST_KEY % '*')}
    if cached_ids != set(references):
        problems.append("post keys: %d not in any feed, %d missing" % (
            len(cached_ids - set(references)),
            len(set(references) - cached_ids)))

    refcounts = {int(member): score for member, score in
                 conn.zrange(POST_SET_KEY, 0, -1, withscores=True)}
    if refcounts != references:
        wrong = sorted(set(refcounts) ^ set(references) |
                       {n for n in refcounts.keys() & references.keys()
                        if refcounts[n] != references[n]})
        problems.append("%s: %d post(s) counted wrongly, e.g. %s" % (
            POST_SET_KEY, len(wrong), wrong[:5]))

    posts = Post.objects.filter(id__in=references).select_related(
            'topic', 'topic__forum', 'user')
    stale = [POST_KEY % post.id for post in posts
             if conn.get(POST_KEY % post.id) != _serialize_post(post)]
    if stale:
        problems.append("%d cached post(s) are not the post as it is now, "
                        "e.g. %s" % (len(stale), ', '.join(stale[:5])))

    # The updated topics: the most recently active, newest first.
    topic_posts = _expected_topic_posts(public_forums)
    expected = [post.topic.id for post in topic_posts]
    actual = [int(n) for n in conn.zrevrange(UPDATED_TOPICS_SET_KEY, 0, -1)]
    if actual != expected:
        problems.append(_describe_list(UPDATED_TOPICS_SET_KEY, actual,
                                       expected))
    for post in topic_posts:
        key = UPDATED_TOPIC_KEY % post.topic.id
        topic_json = conn.get(key)
        if topic_json is None or json.loads(topic_json) != _topic_content(post):
            problems.append("%s is not the topic as it is now" % key)

    post_count, topic_count = _expected_counts(public_forums)
    for key, expected in ((POST_COUNT_KEY, post_count),
                          (TOPIC_COUNT_KEY, topic_count)):
        actual = conn.get(key)
        if actual is None or int(actual) != expected:
            problems.append("%s is %s, expected %d" % (key, actual, expected))

    return problems


def _describe_list(key, actual, expected):
    """One line saying how a list of IDs in Redis differs from the expected one."""
    for n, (held, wanted) in enumerate(zip(actual, expected)):
        if held != wanted:
            break
    else:
        n = min(len(actual), len(expected))
    held = actual[n] if n < len(actual) else None
    wanted = expected[n] if n < len(expected) else None
    return "%s holds %d ID(s), expected %d; first difference at position " \
           "%d: %s, expected %s" % (key, len(actual), len(expected), n, held,
                                    wanted)


def _public_forum_ids():
    # Not Forum.objects.public_forum_ids(): that reads the cache, which after a
    # restore may still describe the old database.
    return list(Forum.objects.filter(
        category__groups__isnull=True).values_list('id', flat=True))


def _expected_feeds(public_forums):
    """
    The feeds the database implies, as a dict of Redis key to post IDs, newest
    first. A forum with no posts has no feed.

    """
    posts = Post.objects.order_by('-creation_date', '-id')
    feeds = {
        ALL_FORUMS_RSS_KEY: list(posts.filter(
            topic__forum__in=public_forums).values_list(
                'id', flat=True)[:MAX_POSTS]),
    }
    for forum_id in public_forums:
        ids = list(posts.filter(topic__forum=forum_id).values_list(
                'id', flat=True)[:MAX_POSTS])
        if ids:
            feeds[FORUM_RSS_KEY % forum_id] = ids
    return feeds


def _expected_topic_posts(public_forums):
    """The newest post of each of the most recently active topics, newest first."""
    topics = Topic.objects.filter(
            forum__in=public_forums, last_post__isnull=False).select_related(
            'last_post', 'last_post__user', 'last_post__topic').order_by(
            '-last_post__creation_date', '-last_post__id')
    return [topic.last_post for topic in topics[:MAX_UPDATED_TOPICS]]


def _expected_counts(public_forums):
    """The public post and topic counts, in that order."""
    return (Post.objects.filter(topic__forum__in=public_forums).count(),
            Topic.objects.filter(forum__in=public_forums).count())


def get_latest_posts(num_posts=MAX_POSTS, forum_id=None):
    """
    This function retrieves num_posts latest posts for the forum with the given
    forum_id. If forum_id is None, the posts are retrieved from the combined
    forums datastore. A list of dictionaries is returned. Each dictionary
    contains information about a post.

    """
    key = FORUM_RSS_KEY % forum_id if forum_id else ALL_FORUMS_RSS_KEY

    num_posts = max(0, min(MAX_POSTS, num_posts))

    if num_posts == 0:
        return []

    conn = get_redis_connection()
    post_ids = conn.lrange(key, 0, num_posts - 1)
    if not post_ids:
        return []

    post_keys = [POST_KEY % n for n in post_ids]
    raw_posts = conn.mget(post_keys)
    raw_posts = [s for s in raw_posts if s is not None]

    posts = []
    for raw_post in raw_posts:
        post = json.loads(raw_post)

        # fix up the pubdate; turn it back into a datetime object
        post['pubdate'] = _deserialize_date(post['pubdate'])

        posts.append(post)

    return posts


def _deserialize_date(pubdate):
    return dateutil.parser.parse(pubdate)


def _deserialize_topic_date(score):
    """Turn an updated-topic score back into the instant it was taken from."""
    # The tz argument is what makes this the inverse of the timestamp() call in
    # _update_latest_topics(); without it the value comes back naive and in
    # whatever zone the container is set to.
    return datetime.datetime.fromtimestamp(score, datetime.timezone.utc)


@receiver(topic_content_update, dispatch_uid='forums.latest_posts')
def on_topic_update(sender, **kwargs):
    """
    This function is our signal handler, called when a topic has been updated
    or created.

    We kick off a Celery task to perform work outside of the request/response
    cycle.

    """
    if kwargs['created']:
        forums.tasks.new_topic_task.delay(sender.id)
    else:
        forums.tasks.updated_topic_task.delay(sender.id)


def process_new_topic(topic_id):
    """
    This function contains new topic processing. Currently we only update the
    topic count statistic.

    """
    try:
        topic = Topic.objects.select_related().get(pk=topic_id)
    except Topic.DoesNotExist:
        logger.warning("process_new_topic: topic %d does not exist", topic_id)
        return

    # selectively process topics from non-public forums
    public_forums = Forum.objects.public_forum_ids()

    if topic.forum.id not in public_forums:
        return

    # update the topic count statistic
    conn = get_redis_connection()

    result = conn.incr(TOPIC_COUNT_KEY)
    if result == 1:
        # it is likely redis got trashed, so re-compute the correct value

        count = Topic.objects.filter(forum__in=public_forums).count()
        conn.set(TOPIC_COUNT_KEY, count)


def process_updated_topic(topic_id):
    """
    This function contains updated topic processing. Update the title only.

    """
    conn = get_redis_connection()
    key = UPDATED_TOPIC_KEY % topic_id
    topic_json = conn.get(key)
    if topic_json is not None:
        try:
            topic = Topic.objects.get(pk=topic_id)
        except Topic.DoesNotExist:
            logger.warning("topic %d does not exist", topic_id)
            return

        topic_dict = json.loads(topic_json)

        if topic.name != topic_dict['title']:
            topic_dict['title'] = topic.name
            topic_json = json.dumps(topic_dict)
            conn.set(key, topic_json)


def get_stats():
    """
    This function returns the topic and post count statistics as a tuple, in
    that order. If a statistic is not available, its position in the tuple will
    be None.

    """
    try:
        conn = get_redis_connection()
        result = conn.mget(TOPIC_COUNT_KEY, POST_COUNT_KEY)
    except redis.RedisError as e:
        logger.error(e)
        return (None, None)

    topic_count = int(result[0]) if result[0] else None
    post_count = int(result[1]) if result[1] else None

    return (topic_count, post_count)


def get_latest_topic_ids(num):
    """
    Return a list of topic ids from the latest topics that have posts. The ids
    will be sorted from newest to oldest.

    """
    try:
        conn = get_redis_connection()
        result = conn.zrevrange(UPDATED_TOPICS_SET_KEY, 0, num - 1)
    except redis.RedisError as e:
        logger.error(e)
        return []

    return [int(n) for n in result]


def get_latest_topics(num):
    """
    Return a list of dictionaries with information about the latest topics that
    have updated posts. The topics are sorted from newest to oldest.

    """
    try:
        conn = get_redis_connection()
        result = conn.zrevrange(UPDATED_TOPICS_SET_KEY, 0, num - 1)

        topic_keys = [UPDATED_TOPIC_KEY % n for n in result]
        json_list = conn.mget(topic_keys) if topic_keys else []

    except redis.RedisError as e:
        logger.error(e)
        return []

    topics = []
    for s in json_list:
        item = json.loads(s)
        item['date'] = _deserialize_topic_date(item['date'])
        topics.append(item)

    return topics


def notify_topic_delete(topic):
    """
    This function should be called when a topic is deleted. It will remove the
    topic from the updated topics set, if present, and delete any info we have
    about the topic.

    Note we don't do anything like this for posts. Since they just populate RSS
    feeds we'll let them 404. The updated topic list is seen in a prominent
    template tag however, so it is a bit more important to get that cleaned up.

    """
    try:
        conn = get_redis_connection()
        pipeline = conn.pipeline()
        pipeline.zrem(UPDATED_TOPICS_SET_KEY, topic.id)
        pipeline.delete(UPDATED_TOPIC_KEY % topic.id)
        pipeline.execute()
    except redis.RedisError as e:
        logger.error(e)


def _serialize_post(post):
    """Serialize a post to JSON and return it.

    """
    # Use absolute URLs for smileys for RSS. This means we have to reconvert the
    # post Markdown to HTML.
    content = site_markup(post.body, relative_urls=False)

    # get any attachments for the post
    attachments = Attachment.objects.filter(post=post).select_related(
            'embed').order_by('order')
    embeds = [item.embed for item in attachments]
    if len(embeds):
        content = render_to_string('forums/post_rss.html', {
            'content': content,
            'embeds': embeds,
        })

    # serialize post attributes
    post_content = {
        'id': post.id,
        'title': post.topic.name,
        'content': content,
        'author': post.user.username,
        'pubdate': post.creation_date.isoformat(),
        'forum_name': post.topic.forum.name,
        'url': post.get_absolute_url()
    }

    return json.dumps(post_content)


# Down here to avoid a circular import
import forums.tasks
