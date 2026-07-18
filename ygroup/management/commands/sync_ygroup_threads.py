"""
sync_ygroup_threads.py - A management command to synchronize the yahoo group
archives by recomputing the de-normalized fields in the thread objects.

"""
from django.core.management.base import BaseCommand, CommandError

from ygroup.models import Thread, Post
import ygroup.views


class Command(BaseCommand):
    help = """\
This command synchronizes the ygroup application's thread objects
by updating their de-normalized fields.
"""

    def add_arguments(self, parser):
        parser.add_argument("-p", "--progress", action="store_true",
            help="Output a . after every 50 threads to show progress")

    def handle(self, *args, **opts):

        show_progress = opts.get('progress', False) or False

        n = 0
        for thread in Thread.objects.iterator():
            thread.post_count = Post.objects.filter(thread=thread).count()
            thread.page = n / ygroup.views.THREADS_PER_PAGE + 1
            thread.save()
            n += 1
            if n % 50 == 0:
                self.stdout.write('.')
                self.stdout.flush()

        self.stdout.write('\n')

