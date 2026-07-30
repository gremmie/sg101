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

"""
import datetime
import time

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import prefetch_related_objects

from search.documents import all_documents
from search.documents import document_for_model
from search.models import SEARCH_VECTOR
from search.models import SearchDocument


# The columns build() supplies, in the order bulk_update should write them.
DOCUMENT_FIELDS = ['title', 'summary', 'author', 'url', 'date', 'indexed_at']

# Rows per batch: one transaction, one round of queries, one progress step.
BATCH_SIZE = 1000

# How often to report progress within a type, in rows.
PROGRESS_INTERVAL = 25000


def batched(iterable, size):
    """Yields lists of up to size items from iterable."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


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
        content_type = ContentType.objects.get_for_model(document.model)

        # order_by() drops the model's Meta ordering: a full sweep does not care
        # what order it walks the table in, and sorting 463k rows to ignore the
        # result is pure cost.
        queryset = document.get_queryset().order_by()
        expected = queryset.count()
        self.report("%s: %d to index" % (label, expected))

        start = time.time()
        indexed = milestone = 0
        # iterator() streams from a server-side cursor, so the source table is
        # never held in memory. Each batch is then its own transaction: a
        # failure at row 400,000 leaves the first 399,999 written.
        for batch in batched(queryset.iterator(chunk_size=batch_size),
                             batch_size):
            with transaction.atomic():
                self.write_batch(document, content_type, batch)
            indexed += len(batch)
            if indexed - milestone >= PROGRESS_INTERVAL:
                milestone = indexed
                self.report("  %s: %d/%d (%s)" % (label, indexed, expected,
                                                  elapsed(time.time() - start)),
                            level=2)

        removed = self.discard_stale(document, content_type)
        self.report("  %s: %d indexed, %d removed, %s" % (
            label, indexed, removed, elapsed(time.time() - start)))
        return indexed

    def write_batch(self, document, content_type, batch):
        """Creates or updates the index rows for one batch of objects."""
        # iterator() ignores prefetch_related, so the batch prefetches its own.
        if document.prefetch:
            prefetch_related_objects(batch, *document.prefetch)

        object_ids = [obj.pk for obj in batch]
        rows = SearchDocument.objects.filter(content_type=content_type,
                                             object_id__in=object_ids)
        existing = dict(rows.values_list('object_id', 'pk'))

        now = datetime.datetime.now()
        create, update = [], []
        for obj in batch:
            values = document.build(obj)
            values['indexed_at'] = now
            row = SearchDocument(content_type=content_type, object_id=obj.pk,
                                 pk=existing.get(obj.pk), **values)
            (update if row.pk else create).append(row)

        SearchDocument.objects.bulk_create(create)
        SearchDocument.objects.bulk_update(update, DOCUMENT_FIELDS)

        # The vector is a function of the columns just written, so PostgreSQL
        # builds it in place for the whole batch rather than sending 1000
        # tsvectors over the wire.
        rows.update(search_vector=SEARCH_VECTOR)

    def discard_stale(self, document, content_type):
        """
        Deletes this type's rows that the source queryset no longer yields.

        That covers a deleted object and an object that has left the indexable
        set some other way -- a forum category being made private takes its
        topics and posts out of the queryset, and this is what takes them out
        of the index.

        """
        stale = SearchDocument.objects.filter(content_type=content_type).exclude(
                object_id__in=document.get_queryset().values('pk'))
        count, _ = stale.delete()
        return count

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
