"""
clean_last_visit is a custom manage.py command.
It is intended to be called from a cron job to clean out old user and anonymous
last visit records.

"""
import datetime

from django.core.management.base import NoArgsCommand

from core.models import UserLastVisit, AnonLastVisit

USER_LV_AGE = datetime.timedelta(weeks=4)
ANON_LV_AGE = datetime.timedelta(days=1)


class Command(NoArgsCommand):
    help = "Run periodically to clean out old last visit records."

    def handle_noargs(self, **options):

        now = datetime.datetime.now()
        user_cut_off = now - USER_LV_AGE
        anon_cut_off = now - ANON_LV_AGE

        UserLastVisit.objects.filter(last_visit__lte=user_cut_off).delete()
        AnonLastVisit.objects.filter(last_visit__lte=anon_cut_off).delete()
