"""
rename_tag.py - Renames a news tag everywhere it appears.

The admin has no way to do this. It used to offer one, and it half-worked: the
shared tag row was renamed while each story kept its own copy of the old string,
so the next save of any affected story quietly put the old tag back and split
the set across two tag pages. Tags are stored on the story now, so there is one
copy and a rename is one write.

"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from news.retag import retag, tag_in_use


class Command(BaseCommand):
    help = "Renames a news tag on every story that carries it."

    def add_arguments(self, parser):
        parser.add_argument('old', help='the tag to rename')
        parser.add_argument('new', help='what to rename it to')
        parser.add_argument('--dry-run', action='store_true',
                            help='report what would change and write nothing')

    def handle(self, *args, **opts):
        # Tags are stored lowercased and every tag URL resolves against the
        # lowercase name, so a capital here would make an unreachable tag.
        old, new = opts['old'].lower(), opts['new'].lower()
        dry_run = opts['dry_run']

        if old == new:
            raise CommandError('"%s" is already its own name.' % old)
        if ' ' in new:
            raise CommandError('A tag cannot contain a space: "%s".' % new)
        if not tag_in_use(old):
            raise CommandError('No story carries the tag "%s".' % old)
        if tag_in_use(new):
            raise CommandError(
                '"%s" is already in use, so this would merge the two rather '
                'than rename one. Use `merge_tags %s %s` if that is what you '
                'meant.' % (new, old, new))

        with transaction.atomic():
            counts = retag(old, new, dry_run=dry_run)

        report(self, counts, '%s "%s" to "%s"' % (
            'Would rename' if dry_run else 'Renamed', old, new), dry_run)


def report(command, counts, headline, dry_run):
    """Shared by both commands: what changed, per model, or that nothing did."""
    total = sum(counts.values())
    if not total:
        command.stdout.write('Nothing to do.')
        return

    command.stdout.write('%s on %d %s:' % (
        headline, total, 'story' if total == 1 else 'stories'))
    for model, count in counts.items():
        if count:
            name = model._meta.verbose_name if count == 1 else \
                   model._meta.verbose_name_plural
            command.stdout.write('   %d %s' % (count, name))
    if dry_run:
        command.stdout.write('Dry run: nothing was written.')
