"""
update_forum_stats.py - A management command to calculate and update the
cache with the forum statistics. These are done out of the request /
response cycle because doing a count on the Post table is expensive
under MySQL and InnoDb.

"""
from django.core.management.base import NoArgsCommand, CommandError

from forums.stats import update_stats


class Command(NoArgsCommand):
    help = "Calculates and updates the cache with forums statistics"

    def handle_noargs(self, **opts):
        update_stats()
