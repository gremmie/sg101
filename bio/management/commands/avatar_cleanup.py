"""avatar_cleanup - a management command to remove orphaned avatar files."""

import os

from django.core.management.base import BaseCommand
from django.conf import settings

from bio.models import UserProfile


class Command(BaseCommand):
    help = "Finds and optionally deletes orphan avatar files"

    def add_arguments(self, parser):
        parser.add_argument('--delete',
                action='store_true',
                dest='delete',
                default=False,
                help='Delete orphan files')

    def handle(self, *args, **options):
        """Find and optionally delete orphan avatar files."""

        delete = options.get('delete', False)

        orphans = set()
        missing = []

        avatar_dir = os.path.join(settings.MEDIA_ROOT, settings.AVATAR_DIR)
        default_avatar = os.path.join(avatar_dir,
                settings.AVATAR_DEFAULT_URL.split('/')[-1])

        # find the set of all files in the downloads area
        for root, dirs, files in os.walk(avatar_dir, followlinks=True):
            for name in files:
                orphans.add(unicode(os.path.join(root, name), 'utf-8'))

        try:
            orphans.remove(default_avatar)
        except KeyError:
            self.stderr.write("Default avatar file missing!  - {}\n".format(
                default_avatar))

        # examine the UserProfile objects
        for profile in UserProfile.objects.iterator():
            if profile.avatar:
                try:
                    orphans.remove(profile.avatar.path)
                except KeyError:
                    missing.append(profile)

        if orphans and delete:
            for path in orphans:
                self.stdout.write("Deleting: {}\n".format(path))
                os.remove(path)
        elif orphans:
            self.stdout.write("Orphan files:\n")
            for orphan in orphans:
                self.stdout.write("{}\n".format(orphan))

        if missing:
            self.stdout.write("Users with missing avatar files:\n")
            for profile in missing:
                self.stdout.write("{}\n".format(profile.user.username))

        empty_dirs = []
        # check for empty directories after deletions
        for root, dirs, files in os.walk(avatar_dir, followlinks=True):
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
