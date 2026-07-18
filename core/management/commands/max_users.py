"""
max_users is a custom manage.py command.
It is intended to be called from a cron job to calculate the maximum
number of users online statistic.
"""
import datetime

from django.core.management.base import BaseCommand

from core.whos_online import max_users


class Command(BaseCommand):
    help = "Run periodically to compute the max users online statistic."

    def handle(self, *args, **options):
        max_users()
