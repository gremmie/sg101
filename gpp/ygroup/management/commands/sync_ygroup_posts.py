"""
sync_ygroup_posts.py - A management command to synchronize the yahoo group
archives by recomputing the de-normalized fields in the post objects.

"""
import optparse

from django.core.management.base import NoArgsCommand, CommandError
from django.core.urlresolvers import reverse

from ygroup.models import Thread, Post
import ygroup.views


class Command(NoArgsCommand):
    help = """\
This command synchronizes the ygroup application's post objects
by updating their de-normalized fields.
"""
    option_list = NoArgsCommand.option_list + (
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 100 posts to show progress"),
    )

    def handle_noargs(self, **opts):

        show_progress = opts.get('progress', False) or False

        threads = {}
        self.stdout.write("Processing threads...\n")
        for thread in Thread.objects.iterator():
            threads[thread.id] = [reverse('ygroup-thread_view', args=[thread.id]),
                list(Post.objects.filter(thread=thread).values_list('id', flat=True))]

        self.stdout.write("Processing posts...\n")
        n = 0
        for post in Post.objects.iterator():
            thread = threads[post.thread.id]
            pos = thread[1].index(post.id)
            page = pos / ygroup.views.POSTS_PER_PAGE + 1
            if page == 1:
                post.thread_url = thread[0] + '#p%d' % (post.id, )
            else:
                post.thread_url = thread[0] + '?page=%d#p%d' % (page, post.id)
            post.save()

            n += 1
            if show_progress and n % 100 == 0:
                self.stdout.write('.')
                self.stdout.flush()

        self.stdout.write('\n')

