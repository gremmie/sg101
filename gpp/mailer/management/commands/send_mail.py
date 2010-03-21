"""send_mail is a custom manage.py command for the mailer application.
It is intended to be called from a cron job periodically to send out queued
email in bulk. This avoids doing the mailing on the HTTP request processing.
"""
from django.core.management.base import NoArgsCommand

import mailer


class Command(NoArgsCommand):
    help = "Run periodically to send out queued email."

    def handle_noargs(self, **options):
        mailer.send_queued_mail()

