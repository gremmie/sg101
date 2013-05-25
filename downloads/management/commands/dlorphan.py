"""dlorphan - a management command to remove orphaned downloads files."""

from optparse import make_option
import os

from django.core.management.base import NoArgsCommand
from django.conf import settings

from downloads.models import Download, PendingDownload


class Command(NoArgsCommand):
    help = "Finds and optionally deletes orphan downloads files"
    option_list = NoArgsCommand.option_list + (
            make_option('--delete',
                action='store_true',
                dest='delete',
                default=False,
                help='Delete orphan files'),
    )

    def handle_noargs(self, **options):
        """Find and optionally delete orphan downloads files."""

        delete = options.get('delete', False)

        orphans = set()
        missing_pending = []
        missing_dls = []
        empty_dirs = []

        dls_dir = os.path.join(settings.MEDIA_ROOT, 'downloads')
        # find the set of all files in the downloads area
        for root, dirs, files in os.walk(dls_dir, followlinks=True):
            for name in files:
                orphans.add(unicode(os.path.join(root, name), 'utf-8'))

            # check for empty directories
            if not len(dirs) and not len(files):
                empty_dirs.append(root)

        # examine the pending downloads:
        for dl in PendingDownload.objects.iterator():
            try:
                orphans.remove(dl.file.path)
            except KeyError:
                missing_pending.append(dl)

        # examine the downloads:
        for dl in Download.objects.iterator():
            try:
                orphans.remove(dl.file.path)
            except KeyError:
                missing_dls.append(dl)

        if orphans:
            print "Orphan files:"
            for orphan in orphans:
                print orphan

        if empty_dirs:
            print "Empty directories:"
            for d in empty_dirs:
                print d

        if missing_pending:
            print "PendingDownloads with missing files:"
            for dl in missing_pending:
                print dl

        if missing_dls:
            print "Downloads with missing files:"
            for dl in missing_dls:
                print dl

        if delete:
            for path in orphans:
                print "Deleting: {}".format(path)
                os.remove(path)

            for path in empty_dirs:
                print "Deleting: {}".format(path)
                os.removedirs(path)
