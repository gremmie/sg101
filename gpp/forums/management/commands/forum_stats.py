"""
forum_stats is a custom manage.py command for the forums application. 
It is intended to be called from a cron job to calculate various forum
statistics.
"""
from django.core.management.base import NoArgsCommand
from django.core.cache import cache

from forums.models import Statistic
import forums.middleware


class Command(NoArgsCommand):
    help = "Run periodically to gather forum statistics."

    def handle_noargs(self, **options):
        # update maximum users online statistic
        users_online = cache.get(forums.middleware.USERS_ONLINE_KEY)
        if users_online:
            try:
                stats = Statistic.objects.get(pk=1)
            except Statistic.DoesNotExist:
                stats = Statistic(max_users=0)

            curr_users = len(users_online)

            if curr_users > stats.max_users:
                stats.max_users = curr_users
                stats.save()
