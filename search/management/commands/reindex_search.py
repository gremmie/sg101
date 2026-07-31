"""
reindex_search.py - A management command to rebuild the search index.

This is the bulk path: it walks the registry's querysets and writes one index
row per object, in batches. It is what populated the index in the first place,
and it stays the answer to the two situations no signal can handle -- the
weights changed, so every row has to be recomputed, and the worker was down,
so rows exist for edits that fired no task anyone can replay.

A run rebuilds whole document types. Rows are matched to their source object by
(content_type, object_id) and updated in place, so a run is safe to repeat; rows
whose source object has since been deleted -- or has become private -- are
removed at the end of their type's pass.

The writing itself lives in search.indexer, which the incremental path shares.

"""
import datetime
import time

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from search.documents import all_documents
from search.documents import document_for_model
from search.indexer import BATCH_SIZE
from search.indexer import discard_stale
from search.indexer import index_queryset
from search.models import SearchDocument


# How often to report progress within a type, in rows.
PROGRESS_INTERVAL = 25000


class Command(BaseCommand):
    help = "Rebuilds the search index from the searchable models."

    def add_arguments(self, parser):
        parser.add_argument('--model', action='append', dest='models',
                metavar='APP.MODEL', default=None,
                help="Rebuild only this document type, e.g. forums.post. "
                     "May be given more than once. The default is every type.")
        parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                metavar='N',
                help="Rows to write per transaction (default %d)." % BATCH_SIZE)

    def handle(self, *args, **opts):
        if opts['batch_size'] < 1:
            raise CommandError("--batch-size must be at least 1")

        self.verbosity = opts['verbosity']
        documents = self.documents_for(opts['models'])
        full_run = opts['models'] is None

        start = time.time()
        total = 0
        for document in documents:
            total += self.reindex(document, opts['batch_size'])

        if full_run:
            self.discard_unregistered_types()

        self.report("%d documents in %s" % (total, elapsed(time.time() - start)))

    def documents_for(self, labels):
        """Returns the documents to rebuild, in registry order."""
        if labels is None:
            return all_documents()

        documents = []
        for label in labels:
            try:
                model = apps.get_model(label)
            except (LookupError, ValueError) as e:
                raise CommandError("%s: %s" % (label, e))
            try:
                documents.append(document_for_model(model))
            except KeyError:
                raise CommandError("%s is not a searchable model" % label)
        return documents

    def reindex(self, document, batch_size):
        """Rebuilds every index row for one document type; returns the count."""
        label = document.model._meta.label_lower
        queryset = document.get_queryset()
        expected = queryset.count()
        self.report("%s: %d to index" % (label, expected))

        start = time.time()
        self.milestone = 0

        def progress(indexed):
            if indexed - self.milestone >= PROGRESS_INTERVAL:
                self.milestone = indexed
                self.report("  %s: %d/%d (%s)" % (label, indexed, expected,
                                                  elapsed(time.time() - start)),
                            level=2)

        indexed = index_queryset(document, queryset, batch_size, progress)
        removed = discard_stale(document)
        self.report("  %s: %d indexed, %d removed, %s" % (
            label, indexed, removed, elapsed(time.time() - start)))
        return indexed

    def discard_unregistered_types(self):
        """Deletes rows left behind by a model that is no longer searchable."""
        registered = [ContentType.objects.get_for_model(document.model).pk
                      for document in all_documents()]
        count, _ = SearchDocument.objects.exclude(
                content_type__in=registered).delete()
        if count:
            self.report("%d rows of unregistered types removed" % count)

    def report(self, message, level=1):
        if self.verbosity >= level:
            self.stdout.write(message)


def elapsed(seconds):
    """Formats a duration the way a person reads a progress line."""
    return str(datetime.timedelta(seconds=round(seconds)))
