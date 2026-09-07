"""
merge_tags.py - Folds one news tag into another.

The counterpart to rename_tag, and the operation the old admin could not do at
all: the tag names were a unique column, so renaming one onto another raised an
IntegrityError. A story carrying both tags keeps the destination once.

"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from news.management.commands.rename_tag import report
from news.retag import retag, tag_in_use


class Command(BaseCommand):
    help = "Folds one news tag into another, on every story that carries it."

    def add_arguments(self, parser):
        parser.add_argument('source', help='the tag to fold away')
        parser.add_argument('destination', help='the tag to fold it into')
        parser.add_argument('--dry-run', action='store_true',
                            help='report what would change and write nothing')

    def handle(self, *args, **opts):
        source = opts['source'].lower()
        destination = opts['destination'].lower()
        dry_run = opts['dry_run']

        if source == destination:
            raise CommandError('"%s" cannot be merged into itself.' % source)
        if not tag_in_use(source):
            raise CommandError('No story carries the tag "%s".' % source)
        # The pair is exhaustive on purpose: rename refuses when the target
        # exists, merge refuses when it does not, so exactly one of them is the
        # right command for any two tags.
        if not tag_in_use(destination):
            raise CommandError(
                'No story carries "%s", so this would rename rather than merge. '
                'Use `rename_tag %s %s` if that is what you meant.'
                % (destination, source, destination))

        with transaction.atomic():
            counts = retag(source, destination, dry_run=dry_run)

        report(self, counts, '%s "%s" into "%s"' % (
            'Would merge' if dry_run else 'Merged', source, destination),
            dry_run)
