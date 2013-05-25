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

        dls_dir = os.path.join(settings.MEDIA_ROOT, 'downloads')
        # find the set of all files in the downloads area
        for root, dirs, files in os.walk(dls_dir, followlinks=True):
            for name in files:
                orphans.add(unicode(os.path.join(root, name), 'utf-8'))

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

        if orphans and delete:
            for path in orphans:
                self.stdout.write("Deleting: {}\n".format(path))
                os.remove(path)
        elif orphans:
            self.stdout.write("Orphan files:\n")
            for orphan in orphans:
                self.stdout.write("{}\n".format(orphan))

        if missing_pending:
            self.stdout.write("PendingDownloads with missing files:\n")
            for dl in missing_pending:
                self.stdout.write("{}\n".format(dl))

        if missing_dls:
            self.stdout.write("Downloads with missing files:\n")
            for dl in missing_dls:
                self.stdout.write("{}\n".format(dl))

        empty_dirs = []
        # check for empty directories after deletions
        for root, dirs, files in os.walk(dls_dir, followlinks=True):
            if not len(dirs) and not len(files):
                empty_dirs.append(root)

        if empty_dirs and delete:
            for path in empty_dirs:
                self.stdout.write("Deleting empty dir: {}\n".format(path))
                os.removedirs(path)
        elif empty_dirs:
            self.stdout.write("Empty directories:\n")
            for d in empty_dirs:
                self.stdout.write("{}\n".format(d))
