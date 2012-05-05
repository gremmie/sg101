"""
pick_potd is a custom manage.py command for the POTD application.
Calling it will pick a new POTD.

"""
from django.core.management.base import NoArgsCommand

from potd.tools import pick_potd


class Command(NoArgsCommand):
    help = "Chooses the next POTD."

    def handle_noargs(self, **options):
        pick_potd()
