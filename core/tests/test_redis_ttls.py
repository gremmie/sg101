"""The TTL inventory that `maxmemory-policy volatile-lru` rests on.

`volatile-lru` evicts only keys that carry a TTL. That is what lets one
server-wide policy serve a Redis holding three unrelated things: the cache
(db 2, where every entry expires and losing one costs a database query), the
Celery broker (db 1) and the site's kept state (db 0). The broker and the kept
state survive eviction because they are written *without* an expiry -- which is
a property of the writing code, not of the policy, and so a property a later
change can quietly take away.

Measured against production on 2026-09-20: db 0 held 831 keys, three of them
expiring, and db 1 held three with none. The three are named below. These tests
fail if a fourth appears, because a new expiring key in db 0 is a new key the
cache can evict, and whether that is safe is a question about what the key is
for -- not one the policy can answer.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from banners.models import Banner, Campaign
from banners.templatetags.banner_tags import banner_url
from core.models import Statistic
from core.services import get_redis_connection
from core.whos_online import (CORE_STATS_KEY, get_stats, report_user,
                              report_visitor)
from forums.latest import process_new_post
from forums.models import Forum, Post, Topic
from user_photos.forms import rate_limit


# Everything the site keeps in db 0, by prefix. `core:` covers CORE_STATS_KEY.
KEPT_STATE_PREFIXES = ('whos_online:', 'accounts:', 'forums:', 'banners:',
                       'core:')

# The two key shapes that legitimately expire, and why each is safe or is not.
# Anything else with a TTL is a finding, not a fixture.
EXPIRING_BY_DESIGN = (
    CORE_STATS_KEY,             # derived; get_stats() rebuilds it from the DB
    'user_photos:counts:',      # the upload rate limiter -- see its own test
)


def expiring_by_design(key):
    return any(key == name or key.startswith(name)
               for name in EXPIRING_BY_DESIGN)


class KeptStateTTLTests(TestCase):
    """What the kept-state writers leave behind, driven through a real Redis.

    A mock cannot answer a question about TTLs, so these run against the
    `redis` service the suite already uses (test db 14).
    """
    fixtures = ['forums.json']

    def setUp(self):
        self.conn = get_redis_connection()
        self.flush()
        self.addCleanup(self.flush)

    def flush(self):
        keys = [key for key in self.conn.keys('*')
                if key.startswith(KEPT_STATE_PREFIXES)
                or key.startswith('user_photos:')]
        if keys:
            self.conn.delete(*keys)

    def exercise_the_writers(self):
        """Run every path that writes kept state, and return the keys it made."""
        user = User.objects.create_user('poster', '', 'pw')  # -> accounts:*
        report_user(user.username)
        report_visitor('198.51.100.7')

        forum = Forum.objects.get(slug='shallow-end')
        topic = Topic.objects.create(forum=forum, name='a topic', user=user)
        post = Post.objects.create(topic=topic, user=user, body='surf riff')
        topic.last_post = post
        topic.save()
        process_new_post(post.id)

        # Two banners, not one: the tag hands the first straight back and only
        # pushes the remainder, so a single-banner campaign writes no key.
        campaign = Campaign.objects.create(name='c', slug='c')
        for name in ('a', 'b'):
            Banner.objects.create(campaign=campaign,
                                  image='banners/c/%s.png' % name,
                                  description=name)
        banner_url('c')

        return [key for key in self.conn.keys('*')
                if key.startswith(KEPT_STATE_PREFIXES)]

    def test_the_writers_are_actually_reached(self):
        """Guards the test below: a scan over nothing passes vacuously."""
        keys = self.exercise_the_writers()

        for prefix in KEPT_STATE_PREFIXES:
            if prefix == 'core:':
                continue        # written by max_users(), not by these paths
            with self.subTest(prefix=prefix):
                self.assertTrue([k for k in keys if k.startswith(prefix)],
                                msg='nothing wrote %s' % prefix)

    def test_kept_state_is_written_without_an_expiry(self):
        """The property `volatile-lru` depends on, for db 0."""
        keys = self.exercise_the_writers()

        for key in keys:
            if expiring_by_design(key):
                continue
            with self.subTest(key=key):
                self.assertEqual(self.conn.ttl(key), -1,
                                 msg='%s expires, so the cache can evict it'
                                     % key)


class ExpiringKeyTests(TestCase):
    """The two exceptions, and the difference between them.

    Both carry a TTL and both are therefore evictable. One rebuilds itself and
    one does not, and that -- not the TTL -- is what decides whether eviction
    matters.
    """

    def setUp(self):
        self.conn = get_redis_connection()
        self.conn.delete(CORE_STATS_KEY)
        self.addCleanup(self.conn.delete, CORE_STATS_KEY)

    def test_the_stats_key_expires_and_rebuilds_from_the_database(self):
        """Safe to evict: the database is the record and Redis is the copy."""
        now = timezone.now()
        Statistic.objects.create(id=1, max_users=42, max_users_date=now,
                                 max_anon_users=7, max_anon_users_date=now)

        stats = get_stats(self.conn)                    # populates Redis
        self.assertEqual(stats.max_users, 42)
        self.assertGreater(self.conn.ttl(CORE_STATS_KEY), 0)

        self.conn.delete(CORE_STATS_KEY)                # stand in for eviction

        self.assertEqual(get_stats(self.conn).max_users, 42)
        self.assertGreater(self.conn.ttl(CORE_STATS_KEY), 0)

    def test_the_upload_rate_limiter_expires_and_nothing_rebuilds_it(self):
        """Not safe to evict, and accepted anyway -- deliberately, with a number.

        `user_photos:counts:<username>` is the only expiring key in db 0 that is
        not derived from something else: it counts uploads against
        USER_PHOTOS_RATE_LIMIT, and evicting it hands that member a fresh quota.
        Nothing restores it, because there is nowhere to restore it from.

        This is documented rather than engineered around. Eviction only begins
        once Redis reaches `maxmemory`, and 150 days of production measurement
        put the whole working set near 3 MB against a 256 MB ceiling. The test
        pins the shape so the decision is visible if that ever stops being true.
        """
        key = 'user_photos:counts:someone'
        self.addCleanup(self.conn.delete, key)

        self.assertFalse(rate_limit(key, 2, 3600))
        self.assertGreater(self.conn.ttl(key), 0)

        self.conn.delete(key)                           # stand in for eviction

        self.assertFalse(rate_limit(key, 2, 3600))
        self.assertEqual(self.conn.get(key), '1', msg='the quota came back')
