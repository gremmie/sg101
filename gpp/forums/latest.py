"""
This module maintains the latest posts datastore. The latest posts are often
needed by RSS feeds, "latest posts" template tags, etc. This module listens for
the post_content_update signal, then bundles the post up and stores it by forum
ID in Redis. We also maintain a combined forums list. This allows quick
retrieval of the latest posts and avoids some slow SQL queries.

"""
import datetime
import time

from django.dispatch import receiver
from django.utils import simplejson

from forums.signals import post_content_update
from forums.models import Forum
from core.services import get_redis_connection


# This constant controls how many latest posts per forum we store
MAX_POSTS = 50


@receiver(post_content_update, dispatch_uid='forums.latest_posts')
def on_post_update(sender, **kwargs):
    """
    This function is our signal handler, called when a post has been updated.
    We only care about newly created posts, and ignore updates.

    We serialize a post to JSON then store in two lists in Redis:
        1. The list for the post's parent forum
        2. The combined forum list

    Note that we only store posts from public forums.

    """
    # ignore non-new posts
    if not kwargs['created']:
        return

    # ignore posts from non-public forums
    public_forums = Forum.objects.public_forum_ids()
    if sender.topic.forum.id not in public_forums:
        return

    # serialize post attributes
    post_content = {
        'id': sender.id,
        'title': sender.topic.name,
        'content': sender.html,
        'author': sender.user.username,
        'pubdate': int(time.mktime(sender.creation_date.timetuple())),
        'forum_name': sender.topic.forum.name,
        'url': sender.get_absolute_url()
    }

    s = simplejson.dumps(post_content)

    # store in Redis

    redis = get_redis_connection()
    pipeline = redis.pipeline()

    key = 'forums:latest:%d' % sender.topic.forum.id

    pipeline.lpush(key, s)
    pipeline.ltrim(key, 0, MAX_POSTS - 1)

    # store in the combined feed; yes this wastes some memory storing it twice,
    # but it makes things much easier

    key = 'forums:latest:*'

    pipeline.lpush(key, s)
    pipeline.ltrim(key, 0, MAX_POSTS - 1)

    pipeline.execute()


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
