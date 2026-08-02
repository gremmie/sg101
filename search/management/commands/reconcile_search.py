"""
reconcile_search.py - A management command to check the search index for drift.

The same sweep Beat runs weekly, on demand. A scheduled job you cannot invoke
yourself is much less useful than it looks: the moment anyone suspects the index
is wrong -- after a worker outage, a snapshot reload, or a release that touched
the indexing path -- the question is what the index looks like now, not what it
looked like at half past three on Sunday morning.

It reports and repairs nothing. The remedy for what it finds is reindex_search.

"""
import sys

from django.core.management.base import BaseCommand

from search.reconcile import log_report
from search.reconcile import reconcile


class Command(BaseCommand):
    help = "Reports drift between the search index and the models it indexes."

    def handle(self, *args, **opts):
        report = reconcile()

        # Logged as well as printed, so that a run someone did by hand is in
        # search.log next to the weekly ones rather than only in their terminal.
        log_report(report)

        if opts['verbosity'] >= 1:
            for type_report in report.types:
                self.stdout.write(str(type_report))
            self.stdout.write(str(report))

            if report.private:
                self.stderr.write('%d index rows point at members-only content'
                                  % report.private)

        # Exit non-zero on drift so this can be run from a deploy check and
        # noticed without anyone reading the output. handle()'s return value
        # would only be printed.
        if not report.clean:
            sys.exit(1)
