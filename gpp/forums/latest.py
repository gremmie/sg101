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
import datetime
import logging
import time

from django.dispatch import receiver
from django.utils import simplejson

from forums.signals import post_content_update, topic_content_update
from forums.models import Forum, Topic, Post
from forums.views.subscriptions import notify_topic_subscribers
from forums.tools import auto_favorite, auto_subscribe
from core.services import get_redis_connection

# This constant controls how many latest posts per forum we store
MAX_POSTS = 50

# This controls how many updated topics we track
MAX_UPDATED_TOPICS = 50

# Redis key names:
POST_COUNT_KEY = "forums:public_post_count"
TOPIC_COUNT_KEY = "forums:public_topic_count"
UPDATED_TOPICS_SET_KEY = "forums:updated_topics:set"
UPDATED_TOPIC_KEY = "forums:updated_topics:%s"

logger = logging.getLogger(__name__)


@receiver(post_content_update, dispatch_uid='forums.latest_posts')
def on_post_update(sender, **kwargs):
    """
    This function is our signal handler, called when a post has been updated.
    We only care about newly created posts, and ignore updates.

    We kick off a Celery task to perform work outside of the request/response
    cycle.

    """
    # ignore non-new posts
    if not kwargs['created']:
        return

    # Kick off a Celery task to process this new post
    forums.tasks.new_post_task.delay(sender.id)


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
        redis = get_redis_connection()
        _update_post_feeds(redis, post)
        _update_post_count(redis, public_forums)
        _update_latest_topics(redis, post)

    # send out any email notifications
    notify_topic_subscribers(post, defer=False)

    # perform any auto-favorite and auto-subscribe actions for the new post
    auto_favorite(post)
    auto_subscribe(post)


def _update_post_feeds(redis, post):
    """
    Updates the forum feeds we keep in Redis so that our RSS feeds are quick.

    """
    # serialize post attributes
    post_content = {
        'id': post.id,
        'title': post.topic.name,
        'content': post.html,
        'author': post.user.username,
        'pubdate': int(time.mktime(post.creation_date.timetuple())),
        'forum_name': post.topic.forum.name,
        'url': post.get_absolute_url()
    }

    s = simplejson.dumps(post_content)

    # store in Redis

    pipeline = redis.pipeline()

    key = 'forums:latest:%d' % post.topic.forum.id

    pipeline.lpush(key, s)
    pipeline.ltrim(key, 0, MAX_POSTS - 1)

    # store in the combined feed; yes this wastes some memory storing it twice,
    # but it makes things much easier

    key = 'forums:latest:*'

    pipeline.lpush(key, s)
    pipeline.ltrim(key, 0, MAX_POSTS - 1)

    pipeline.execute()


def _update_post_count(redis, public_forums):
    """
    Updates the post count we cache in Redis. Doing a COUNT(*) on the post table
    can be expensive in MySQL InnoDB.

    """
    result = redis.incr(POST_COUNT_KEY)
    if result == 1:
        # it is likely redis got trashed, so re-compute the correct value

        count = Post.objects.filter(topic__forum__in=public_forums).count()
        redis.set(POST_COUNT_KEY, count)


def _update_latest_topics(redis, post):
    """
    Updates the "latest topics with new posts" list we cache in Redis for speed.
    There is a template tag and forum view that uses this information.

    """
    # serialize topic attributes
    topic_id = post.topic.id
    topic_score = int(time.mktime(post.creation_date.timetuple()))

    topic_content = {
        'title': post.topic.name,
        'author': post.user.username,
        'date': topic_score,
        'url': post.get_absolute_url()
    }
    json = simplejson.dumps(topic_content)
    key = UPDATED_TOPIC_KEY % topic_id

    pipeline = redis.pipeline()
    pipeline.set(key, json)
    pipeline.zadd(UPDATED_TOPICS_SET_KEY, topic_score, topic_id)
    pipeline.zcard(UPDATED_TOPICS_SET_KEY)
    results = pipeline.execute()

    # delete topics beyond our maximum count
    num_topics = results[-1]
    num_to_del = num_topics - MAX_UPDATED_TOPICS
    if num_to_del > 0:
        # get the IDs of the topics we need to delete first
        start = 0
        stop = num_to_del - 1   # Redis indices are inclusive
        old_ids = redis.zrange(UPDATED_TOPICS_SET_KEY, start, stop)

        keys = [UPDATED_TOPIC_KEY % n for n in old_ids]
        redis.delete(*keys)

        # now delete the oldest num_to_del topics
        redis.zremrangebyrank(UPDATED_TOPICS_SET_KEY, start, stop)


def get_latest_posts(num_posts=MAX_POSTS, forum_id=None):
    """
    This function retrieves num_posts latest posts for the forum with the given
    forum_id. If forum_id is None, the posts are retrieved from the combined
    forums datastore. A list of dictionaries is returned. Each dictionary
    contains information about a post.

    """
    key = 'forums:latest:%d' % forum_id if forum_id else 'forums:latest:*'

    num_posts = max(0, min(MAX_POSTS, num_posts))

    if num_posts == 0:
        return []

    redis = get_redis_connection()
    raw_posts = redis.lrange(key, 0, num_posts - 1)

    posts = []
    for raw_post in raw_posts:
        post = simplejson.loads(raw_post)

        # fix up the pubdate; turn it back into a datetime object
        post['pubdate'] = datetime.datetime.fromtimestamp(post['pubdate'])

        posts.append(post)

    return posts


@receiver(topic_content_update, dispatch_uid='forums.latest_posts')
def on_topic_update(sender, **kwargs):
    """
    This function is our signal handler, called when a topic has been updated.
    We only care about newly created topics, and ignore updates.

    We kick off a Celery task to perform work outside of the request/response
    cycle.

    """
    # ignore non-new topics
    if not kwargs['created']:
        return

    # Kick off a Celery task to process this new post
    forums.tasks.new_topic_task.delay(sender.id)


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
    redis = get_redis_connection()

    result = redis.incr(TOPIC_COUNT_KEY)
    if result == 1:
        # it is likely redis got trashed, so re-compute the correct value

        count = Topic.objects.filter(forum__in=public_forums).count()
        redis.set(TOPIC_COUNT_KEY, count)


def get_stats():
    """
    This function returns the topic and post count statistics as a tuple, in
    that order. If a statistic is not available, its position in the tuple will
    be None.

    """
    try:
        redis = get_redis_connection()
        result = redis.mget(TOPIC_COUNT_KEY, POST_COUNT_KEY)
    except redis.RedisError, e:
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
        redis = get_redis_connection()
        result = redis.zrevrange(UPDATED_TOPICS_SET_KEY, 0, num - 1)
    except redis.RedisError, e:
        logger.error(e)
        return []

    return [int(n) for n in result]


def get_latest_topics(num):
    """
    Return a list of dictionaries with information about the latest topics that
    have updated posts. The topics are sorted from newest to oldest.

    """
    try:
        redis = get_redis_connection()
        result = redis.zrevrange(UPDATED_TOPICS_SET_KEY, 0, num - 1)

        topic_keys = [UPDATED_TOPIC_KEY % n for n in result]
        json_list = redis.mget(topic_keys)

    except redis.RedisError, e:
        logger.error(e)
        return []

    topics = []
    for s in json_list:
        item = simplejson.loads(s)
        item['date'] = datetime.datetime.fromtimestamp(item['date'])
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
        redis = get_redis_connection()
        pipeline = redis.pipeline()
        pipeline.zrem(UPDATED_TOPICS_SET_KEY, topic.id)
        pipeline.delete(UPDATED_TOPIC_KEY % topic.id)
        pipeline.execute()
    except redis.RedisError, e:
        logger.error(e)


# Down here to avoid a circular import
import forums.tasks
