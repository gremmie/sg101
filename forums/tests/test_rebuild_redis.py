"""
Tests for rebuilding the Redis state that is derived from the database.

A database restore leaves Redis holding state keyed by IDs the restored database
reuses, so the cached feeds, topics and counts point at the wrong rows. The
`rebuild_redis` command, and the `rebuild()` / `verify()` functions behind it in
forums.latest and accounts.stats, put that state back from the database and
check it.

These run against the real Redis the suite already uses (test db 14). Posts are
created directly rather than through process_new_post, so Redis starts out
wrong, as it does after a restore. The feed and topic caps are patched down to 3
so a handful of posts exercises the trimming.
"""
import datetime
import json
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

import accounts.stats
import forums.latest
from accounts.stats import NEW_USERS_KEY, USER_COUNT_KEY
from core.services import get_redis_connection
from forums.latest import (ALL_FORUMS_RSS_KEY, FORUM_RSS_KEY, POST_COUNT_KEY,
                           POST_KEY, POST_SET_KEY, TOPIC_COUNT_KEY,
                           UPDATED_TOPIC_KEY, UPDATED_TOPICS_SET_KEY,
                           _serialize_post)
from forums.models import Forum, Post, Topic


CAP = 3

# Everything these tests write, so cleanup can find it.
TEST_PREFIXES = ('forums:', 'accounts:', 'banners:', 'core:', 'whos_online:',
                 'user_photos:', 'unrelated:')


class RebuildTestCase(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.conn = get_redis_connection()
        self.flush()
        self.addCleanup(self.flush)
        cache.clear()
        self.addCleanup(cache.clear)

        for name in ('MAX_POSTS', 'MAX_UPDATED_TOPICS'):
            patcher = patch.object(forums.latest, name, CAP)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.user = User.objects.create_user('poster', '', 'pw')
        self.shallow = Forum.objects.get(slug='shallow-end')
        self.gear = Forum.objects.get(slug='gear')
        self.now = timezone.now()

    def flush(self):
        keys = [k for k in self.conn.keys('*') if k.startswith(TEST_PREFIXES)]
        if keys:
            self.conn.delete(*keys)

    def make_post(self, forum, minutes_ago, topic=None, user=None):
        """A post dated `minutes_ago`, in a new topic unless one is given."""
        user = user or self.user
        if topic is None:
            topic = Topic.objects.create(forum=forum, name='topic', user=user)
        post = Post.objects.create(topic=topic, user=user, body='body')
        when = self.now - datetime.timedelta(minutes=minutes_ago)
        Post.objects.filter(pk=post.pk).update(creation_date=when,
                                               update_date=when)
        Topic.objects.filter(pk=topic.pk).update(last_post=post,
                                                 update_date=when)
        return Post.objects.get(pk=post.pk)

    def make_private(self, forum):
        forum.category.groups.add(Group.objects.create(name='Inner Circle'))

    def feed(self, key):
        return [int(n) for n in self.conn.lrange(key, 0, -1)]

    def rebuild(self):
        forums.latest.rebuild(self.conn)
        accounts.stats.rebuild(self.conn)


class ForumsRebuildTests(RebuildTestCase):

    def setUp(self):
        super().setUp()
        # Five posts, alternating forums; minutes_ago 50, 40, 30, 20, 10.
        self.posts = [self.make_post(forum, minutes)
                      for forum, minutes in ((self.shallow, 50),
                                             (self.gear, 40),
                                             (self.shallow, 30),
                                             (self.gear, 20),
                                             (self.shallow, 10))]

    def test_stale_post_keys_and_feed_entries_are_removed(self):
        self.conn.set(POST_KEY % 999999, '{}')
        self.conn.lpush(ALL_FORUMS_RSS_KEY, 999999)
        self.conn.zadd(POST_SET_KEY, {999999: 2})

        self.rebuild()

        self.assertIsNone(self.conn.get(POST_KEY % 999999))
        self.assertNotIn(999999, self.feed(ALL_FORUMS_RSS_KEY))
        self.assertIsNone(self.conn.zscore(POST_SET_KEY, 999999))

    def test_combined_feed_is_the_newest_posts_newest_first(self):
        self.rebuild()
        expected = [p.id for p in reversed(self.posts)][:CAP]
        self.assertEqual(self.feed(ALL_FORUMS_RSS_KEY), expected)

    def test_newest_means_newest_by_date_not_by_id(self):
        # Created last, so it has the highest ID, but dated before them all.
        old = self.make_post(self.gear, 60)
        self.rebuild()
        self.assertNotIn(old.id, self.feed(ALL_FORUMS_RSS_KEY))
        self.assertEqual(forums.latest.verify(self.conn), [])

    def test_each_forum_feed_is_its_newest_posts(self):
        self.rebuild()
        for forum in (self.shallow, self.gear):
            expected = [p.id for p in reversed(self.posts)
                        if p.topic.forum_id == forum.id][:CAP]
            self.assertEqual(self.feed(FORUM_RSS_KEY % forum.id), expected)

    def test_private_forum_posts_are_excluded_everywhere(self):
        classifieds = Forum.objects.get(slug='for-sale-trade')
        self.make_private(classifieds)
        secret = self.make_post(classifieds, 1)

        self.rebuild()

        self.assertNotIn(secret.id, self.feed(ALL_FORUMS_RSS_KEY))
        self.assertFalse(self.conn.exists(FORUM_RSS_KEY % classifieds.id))
        self.assertIsNone(self.conn.get(POST_KEY % secret.id))
        self.assertEqual(int(self.conn.get(POST_COUNT_KEY)), len(self.posts))

    def test_a_stale_cached_public_forum_list_is_not_trusted(self):
        classifieds = Forum.objects.get(slug='for-sale-trade')
        self.make_private(classifieds)
        secret = self.make_post(classifieds, 1)
        # What the cache would hold from before the forum was made private.
        cache.set('public_forum_ids',
                  list(Forum.objects.values_list('id', flat=True)))

        self.rebuild()

        self.assertNotIn(secret.id, self.feed(ALL_FORUMS_RSS_KEY))
        self.assertEqual(forums.latest.verify(self.conn), [])

    def test_reference_counts_count_the_lists_holding_each_post(self):
        self.rebuild()
        combined = set(self.feed(ALL_FORUMS_RSS_KEY))
        held = set()
        for forum in (self.shallow, self.gear):
            held.update(self.feed(FORUM_RSS_KEY % forum.id))
        held.update(combined)

        refcounts = {int(m): s for m, s in
                     self.conn.zrange(POST_SET_KEY, 0, -1, withscores=True)}
        for post_id in held:
            lists = (post_id in combined) + 1
            self.assertEqual(refcounts[post_id], lists, post_id)
        self.assertEqual(set(refcounts), held)

        cached = {int(k.split(':')[-1])
                  for k in self.conn.keys(POST_KEY % '*')}
        self.assertEqual(cached, held)

    def test_cached_posts_match_their_serialization(self):
        self.rebuild()
        for post_id in self.feed(ALL_FORUMS_RSS_KEY):
            post = Post.objects.get(pk=post_id)
            self.assertEqual(self.conn.get(POST_KEY % post_id),
                             _serialize_post(post))

    def test_latest_topics_are_the_most_recently_active(self):
        self.rebuild()
        newest = list(reversed(self.posts))[:CAP]
        ids = [int(n) for n in
               self.conn.zrevrange(UPDATED_TOPICS_SET_KEY, 0, -1)]
        self.assertEqual(ids, [p.topic_id for p in newest])

        for post in newest:
            data = json.loads(self.conn.get(UPDATED_TOPIC_KEY % post.topic_id))
            self.assertEqual(data['title'], post.topic.name)
            self.assertEqual(data['author'], post.user.username)
            self.assertEqual(data['date'],
                             int(post.creation_date.timestamp()))

    def test_stale_topic_entries_are_removed(self):
        self.conn.zadd(UPDATED_TOPICS_SET_KEY, {999999: 10 ** 10})
        self.conn.set(UPDATED_TOPIC_KEY % 999999, '{}')
        self.rebuild()
        self.assertIsNone(self.conn.zscore(UPDATED_TOPICS_SET_KEY, 999999))
        self.assertIsNone(self.conn.get(UPDATED_TOPIC_KEY % 999999))

    def test_counts_are_set_from_the_database(self):
        self.conn.set(POST_COUNT_KEY, 12345)
        self.conn.set(TOPIC_COUNT_KEY, 12345)
        self.rebuild()
        self.assertEqual(int(self.conn.get(POST_COUNT_KEY)), len(self.posts))
        self.assertEqual(int(self.conn.get(TOPIC_COUNT_KEY)), len(self.posts))

    def test_verify_is_empty_after_a_rebuild(self):
        self.rebuild()
        self.assertEqual(forums.latest.verify(self.conn), [])

    def test_verify_reports_a_missing_feed_entry(self):
        self.rebuild()
        self.conn.lpop(ALL_FORUMS_RSS_KEY)
        self.assertNotEqual(forums.latest.verify(self.conn), [])

    def test_verify_reports_altered_post_content(self):
        self.rebuild()
        self.conn.set(POST_KEY % self.posts[-1].id, '{"stale": true}')
        self.assertNotEqual(forums.latest.verify(self.conn), [])

    def test_verify_reports_a_wrong_reference_count(self):
        self.rebuild()
        self.conn.zincrby(POST_SET_KEY, 1, self.posts[-1].id)
        self.assertNotEqual(forums.latest.verify(self.conn), [])

    def test_verify_reports_a_stray_post_key(self):
        self.rebuild()
        self.conn.set(POST_KEY % 999999, '{}')
        self.assertNotEqual(forums.latest.verify(self.conn), [])

    def test_verify_reports_a_wrong_count(self):
        self.rebuild()
        self.conn.incr(TOPIC_COUNT_KEY)
        self.assertNotEqual(forums.latest.verify(self.conn), [])

    def test_verify_reports_a_wrong_latest_topic(self):
        self.rebuild()
        self.conn.zadd(UPDATED_TOPICS_SET_KEY, {self.posts[0].topic_id: 0})
        self.assertNotEqual(forums.latest.verify(self.conn), [])


class AccountsRebuildTests(RebuildTestCase):

    def setUp(self):
        super().setUp()
        # Twelve more users, so the newest ten are a proper subset.
        for n in range(12):
            User.objects.create_user('member%02d' % n, '', 'pw')

    def newest_usernames(self):
        return list(User.objects.order_by('-date_joined', '-id')
                    .values_list('username', flat=True)[:10])

    def test_user_count_and_new_users_are_set_from_the_database(self):
        self.conn.set(USER_COUNT_KEY, 99999)
        self.conn.delete(NEW_USERS_KEY)
        self.conn.rpush(NEW_USERS_KEY, '_email_smoke', '_email_smoke')

        self.rebuild()

        self.assertEqual(int(self.conn.get(USER_COUNT_KEY)),
                         User.objects.count())
        self.assertEqual(self.conn.lrange(NEW_USERS_KEY, 0, -1),
                         self.newest_usernames())

    def test_verify_is_empty_after_a_rebuild(self):
        self.rebuild()
        self.assertEqual(accounts.stats.verify(self.conn), [])

    def test_verify_reports_wrong_new_users(self):
        self.rebuild()
        self.conn.lpush(NEW_USERS_KEY, '_email_smoke')
        self.assertNotEqual(accounts.stats.verify(self.conn), [])

    def test_verify_reports_a_wrong_user_count(self):
        self.rebuild()
        self.conn.incr(USER_COUNT_KEY)
        self.assertNotEqual(accounts.stats.verify(self.conn), [])


class RebuildRedisCommandTests(RebuildTestCase):

    def setUp(self):
        super().setUp()
        self.post = self.make_post(self.shallow, 5)

    def run_command(self, *args):
        out = StringIO()
        call_command('rebuild_redis', *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_clears_derived_keys_and_leaves_the_rest(self):
        self.conn.rpush('banners:url:main', '/stale.png')
        self.conn.hset('core:stats', mapping={'max_users': 1})
        self.conn.zadd('whos_online:users', {'someone': 1})
        self.conn.set('user_photos:counts:someone', 1)
        self.conn.set('unrelated:key', 'kept')

        self.run_command('--noinput')

        self.assertFalse(self.conn.exists('banners:url:main'))
        self.assertFalse(self.conn.exists('core:stats'))
        self.assertTrue(self.conn.exists('whos_online:users'))
        self.assertTrue(self.conn.exists('user_photos:counts:someone'))
        self.assertEqual(self.conn.get('unrelated:key'), 'kept')

    def test_clears_the_django_cache(self):
        cache.set('stale', 'value')
        self.run_command('--noinput')
        self.assertIsNone(cache.get('stale'))

    def test_rebuilds_the_feeds(self):
        self.run_command('--noinput')
        self.assertEqual(self.feed(ALL_FORUMS_RSS_KEY), [self.post.id])
        self.assertEqual(int(self.conn.get(USER_COUNT_KEY)),
                         User.objects.count())

    def test_check_fails_on_stale_state_and_writes_nothing(self):
        self.conn.set(POST_COUNT_KEY, 12345)
        cache.set('stale', 'value')
        before = {k: self.conn.dump(k) for k in self.conn.keys('*')}

        with self.assertRaisesMessage(CommandError, 'does not match'):
            self.run_command('--check')

        after = {k: self.conn.dump(k) for k in self.conn.keys('*')}
        self.assertEqual(after, before)
        self.assertEqual(cache.get('stale'), 'value')

    def test_check_passes_after_a_rebuild(self):
        self.run_command('--noinput')
        self.run_command('--check')

    def test_declining_the_prompt_changes_nothing(self):
        self.conn.set(POST_COUNT_KEY, 12345)
        with patch('builtins.input', return_value='no'):
            with self.assertRaisesMessage(CommandError, 'cancelled'):
                self.run_command()
        self.assertEqual(self.conn.get(POST_COUNT_KEY), '12345')

    def test_noinput_does_not_prompt(self):
        with patch('builtins.input', side_effect=AssertionError('prompted')):
            self.run_command('--noinput')
