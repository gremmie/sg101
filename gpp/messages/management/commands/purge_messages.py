"""
purge_messages is a custom manage.py command for the messages application. 
It is intended to be called from a cron job to purge messages that have been
deleted by both sender and receiver.
"""

from django.core.management.base import NoArgsCommand

from messages.models import Message


class Command(NoArgsCommand):
    help = "Delete messages that have been sent to the trash by both sender and receiver."

    def handle_noargs(self, **options):
        Message.objects.filter(sender_delete_date__isnull=False,
                receiver_delete_date__isnull=False).delete()


# vim: ts=4 sw=4
