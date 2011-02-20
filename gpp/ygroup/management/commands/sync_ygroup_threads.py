"""
sync_ygroup_threads.py - A management command to synchronize the yahoo group
archives by recomputing the de-normalized fields in the thread objects.

"""
import optparse

from django.core.management.base import NoArgsCommand, CommandError

from ygroup.models import Thread, Post
import ygroup.views


class Command(NoArgsCommand):
    help = """\
This command synchronizes the ygroup application's thread objects
by updating their de-normalized fields.
"""
    option_list = NoArgsCommand.option_list + (
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 50 threads to show progress"),
    )

    def handle_noargs(self, **opts):

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

