"""
Characterization tests for the forums "latest posts" datastore and RSS feeds.

forums.latest keeps a Redis-backed cache of the newest posts and recently-updated
topics (populated by a Celery task when a post is created), which the RSS feeds
and homepage template tags read. These tests drive the real datastore: they
process a post, then assert the read-side functions and the syndication feed
surface it.

Redis (test DB 14) persists across tests, so setUp/tearDown flush the forums keys
and clear the page cache to keep each test hermetic.
"""
from django.core.cache import cache
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.test import TestCase

from core.services import get_redis_connection
from forums.latest import (get_latest_posts, get_latest_topic_ids,
                           get_latest_topics, get_stats, notify_topic_delete,
                           process_new_post)
from forums.models import Forum, Post, Topic


def clear_forums_redis(conn):
    keys = conn.keys('forums:*')
    if keys:
        conn.delete(*keys)


def make_post(forum, user, topic_name='a topic', body='hello world'):
    """Create a topic + first post and run it through the latest-posts pipeline."""
    topic = Topic.objects.create(forum=forum, name=topic_name, user=user)
    post = Post.objects.create(topic=topic, user=user, body=body)
    topic.last_post = post
    topic.save()
    process_new_post(post.id)
    return topic, post


class LatestPostsTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.conn = get_redis_connection()
        clear_forums_redis(self.conn)
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.user = User.objects.create_user('poster', '', 'pw')

    def tearDown(self):
        clear_forums_redis(self.conn)
        cache.clear()

    def test_processed_post_appears_in_combined_feed(self):
        topic, post = make_post(self.forum, self.user, body='surf riff')
        posts = get_latest_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['author'], 'poster')
        self.assertIn('surf riff', posts[0]['content'])

    def test_processed_post_appears_in_its_forum_feed(self):
        topic, post = make_post(self.forum, self.user)
        posts = get_latest_posts(forum_id=self.forum.id)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['forum_name'], self.forum.name)

    def test_no_posts_when_nothing_processed(self):
        self.assertEqual(get_latest_posts(), [])

    def test_latest_topics_track_processed_post(self):
        topic, post = make_post(self.forum, self.user, topic_name='Fresh Topic')
        self.assertIn(topic.id, get_latest_topic_ids(10))
        topics = get_latest_topics(10)
        self.assertEqual([t['title'] for t in topics], ['Fresh Topic'])

    def test_notify_topic_delete_removes_from_latest(self):
        topic, post = make_post(self.forum, self.user)
        self.assertIn(topic.id, get_latest_topic_ids(10))

        notify_topic_delete(topic)
        self.assertNotIn(topic.id, get_latest_topic_ids(10))

    def test_get_stats_reports_post_count(self):
        make_post(self.forum, self.user)
        topic_count, post_count = get_stats()
        self.assertEqual(post_count, 1)


class ForumsFeedTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.conn = get_redis_connection()
        clear_forums_redis(self.conn)
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.user = User.objects.create_user('poster', '', 'pw')

    def tearDown(self):
        clear_forums_redis(self.conn)
        cache.clear()

    def test_combined_feed_renders_with_post(self):
        make_post(self.forum, self.user, topic_name='Combined Item')
        response = self.client.get('/feeds/forums/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Combined Item', response.content.decode())

    def test_forum_feed_renders(self):
        make_post(self.forum, self.user, topic_name='Forum Item')
        response = self.client.get('/feeds/forums/%s/' % self.forum.slug)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Forum Item', response.content.decode())

    def test_empty_feed_still_renders(self):
        response = self.client.get('/feeds/forums/')
        self.assertEqual(response.status_code, 200)

    def test_private_forum_feed_is_404(self):
        # A non-public forum (its category has assigned groups) is excluded.
        secret = Group.objects.create(name='Inner Circle')
        self.forum.category.groups.add(secret)
        response = self.client.get('/feeds/forums/%s/' % self.forum.slug)
        self.assertEqual(response.status_code, 404)
