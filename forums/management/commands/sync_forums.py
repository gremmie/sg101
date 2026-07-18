"""
sync_forums.py - A management command to synchronize the forums by recomputing
the de-normalized fields in the forum and topic objects.

"""
from django.core.management.base import BaseCommand, CommandError

from forums.models import Forum
from forums.models import Topic


class Command(BaseCommand):
    help = """\
This command synchronizes the forum application's forums and topic objects
by updating their de-normalized fields.
"""

    def add_arguments(self, parser):
        parser.add_argument("-p", "--progress", action="store_true",
            help="Output a . after every 50 topics to show progress")

    def handle(self, *args, **opts):

        show_progress = opts.get('progress', False) or False

        n = 0
        for topic in Topic.objects.iterator():
            topic.post_count_update()
            topic.save()
            n += 1
            if n % 50 == 0:
                self.stdout.write('.')
                self.stdout.flush()

        for forum in Forum.objects.all():
            forum.sync()
            forum.save()

        self.stdout.write('\n')

