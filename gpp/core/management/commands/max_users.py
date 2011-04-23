"""
max_users is a custom manage.py command.
It is intended to be called from a cron job to calculate the maximum
number of users online statistic.
"""
import datetime

from django.core.management.base import NoArgsCommand

from core.models import Statistic
from core.whos_online import get_users_online, get_visitors_online, tick


class Command(NoArgsCommand):
    help = "Run periodically to compute the max users online statistic."

    def handle_noargs(self, **options):

        now = datetime.datetime.now()

        users = len(get_users_online())
        guests = len(get_visitors_online())

        updated = False
        try:
            stat = Statistic.objects.get(pk=1)
        except Statistic.DoesNotExist:
            stat = Statistic(max_users=users,
                    max_users_date=now,
                    max_anon_users=guests,
                    max_anon_users_date=now)
            updated=True
        else:
            if users > stat.max_users:
                stat.max_users = users
                stat.max_users_date = now
                updated=True
            if guests > stat.max_anon_users:
                stat.max_anon_users = guests
                stat.max_anon_users_date = now
                updated=True

        if updated:
            stat.save()

        # "tick" the who's online data collector
        tick()
