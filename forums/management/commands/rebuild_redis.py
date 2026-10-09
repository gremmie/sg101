"""
rebuild_redis.py - A management command to rebuild the Redis state that is
derived from the database, then check it against the database.

Run it after every database restore. A restore replaces the database and leaves
Redis as it was, still describing the old database under post, topic and user
IDs the restored one reuses: the home page then shows old content under links
that lead to real posts.

What it does, in order:

* clears the Django cache. Every entry in it is derived from the database, and
  the public forum list the rest of the rebuild reads is cached there.
* deletes the banner rotation lists and the cached site statistics, which
  refill themselves from the database on next use.
* rebuilds the forum feeds, updated topics and counts (forums.latest), and the
  user count and newest members (accounts.stats).
* checks all of that against the database.

Who's online and the upload rate limiter are not derived from the database and
are left alone, as is the Celery broker, which is a different Redis database.

Run it with the site in maintenance mode: a post processed by the worker while
the rebuild runs can be missed by it.

"""
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

import accounts.stats
import forums.latest
from banners.templatetags.banner_tags import BANNER_URL_KEY
from core.services import get_redis_connection
from core.whos_online import CORE_STATS_KEY


class Command(BaseCommand):
    help = ("Rebuilds the Redis state derived from the database, as after a "
            "database restore, and checks it against the database.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input', action='store_false',
            dest='interactive',
            help="Do not ask for confirmation before rebuilding.")
        parser.add_argument(
            '--check', action='store_true',
            help="Only check Redis against the database; change nothing.")

    def handle(self, *args, **options):
        conn = get_redis_connection()

        if not options['check']:
            if options['interactive']:
                answer = input(
                    "This clears the cache and replaces the forum and account "
                    "statistics in Redis with what the database says.\n"
                    "Type 'yes' to continue, or 'no' to cancel: ")
                if answer != 'yes':
                    raise CommandError("Rebuild cancelled.")
            self.rebuild(conn)

        problems = forums.latest.verify(conn) + accounts.stats.verify(conn)
        for problem in problems:
            self.stderr.write(problem)
        if problems:
            raise CommandError("Redis does not match the database: %d "
                               "problem(s)." % len(problems))

        self.stdout.write("Redis matches the database.")

    def rebuild(self, conn):
        cache.clear()

        keys = list(conn.scan_iter(BANNER_URL_KEY % '*'))
        keys.append(CORE_STATS_KEY)
        conn.delete(*keys)

        forums.latest.rebuild(conn)
        accounts.stats.rebuild(conn)
