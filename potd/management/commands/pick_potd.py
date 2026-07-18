"""
pick_potd is a custom manage.py command for the POTD application.
Calling it will pick a new POTD.

"""
from django.core.management.base import BaseCommand

from potd.tools import pick_potd


class Command(BaseCommand):
    help = "Chooses the next POTD."

    def handle(self, *args, **options):
        pick_potd()
