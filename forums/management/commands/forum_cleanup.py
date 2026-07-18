"""
forum_cleanup.py - A management command to cleanup forum model objects. Right
now this entails deleting old forum and topic last visit records.

"""
import datetime

from django.core.management.base import BaseCommand

from forums.models import ForumLastVisit, TopicLastVisit
import forums.unread


class Command(BaseCommand):
    help = "This command deletes old forum and topic last visit records."

    def handle(self, *args, **opts):

        now = datetime.datetime.now()
        threshold = now - forums.unread.THRESHOLD * 2

        # delete old topic last visit records
        TopicLastVisit.objects.filter(last_visit__lt=threshold).delete()

        # delete old forum visit records
        ForumLastVisit.objects.filter(end_date__lt=threshold).delete()
