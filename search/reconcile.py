"""
Comparing the search index against the tables it was built from.

This reports drift; it repairs nothing. The incremental path in search.receivers
and search.tasks is supposed to make drift impossible, and the point of this
module is to find out whether that is true. Repairing on discovery would hide
the bugs worth finding -- an index that silently fixes itself every week looks
exactly like an index that was never wrong.

A reconcile is not a rebuild. search.indexer recomputes vectors and is what runs
when the weights change; nothing here computes a vector or writes a row. Every
check is one query that compares sets or timestamps in the database, so the cost
scales with the drift found rather than with the size of the corpus.

The one thing to be careful of when changing these queries: they must be
anti-joins. Spelling `missing` as `exclude(pk__in=rows.values('object_id'))` is
the obvious thing and produces `NOT IN (subquery)`, which PostgreSQL cannot
answer with an anti-join -- three-valued logic means a single NULL would change
the result, so it materializes the subquery and rechecks it per row. That form
had not finished after five minutes on forums.Post. `~Exists(...)` compiles to
`NOT EXISTS` and runs in under a second.

"""
import logging
import time

from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists
from django.db.models import OuterRef

from search.documents import all_documents
from search.models import SearchDocument


# The search log, by name and not by module, so a sweep's findings land in
# search.log beside the queries members ran rather than in the worker's log.
# celery's get_task_logger() cannot be used for this: it reparents the logger it
# returns onto celery.task, which would carry these lines away from the handler
# they are meant for.
logger = logging.getLogger('search')

# How many offending ids to carry with each count. A drift report is something
# someone reads in a log; the count says how bad it is and the sample says where
# to start looking, and neither job is served by 400,000 primary keys.
SAMPLE_SIZE = 10


class Drift:
    """One detection query's result: how many, and a few of them."""

    def __init__(self, count, sample=()):
        self.count = count
        self.sample = list(sample)

    def __bool__(self):
        return bool(self.count)

    def __str__(self):
        if not self.count:
            return '0'
        ids = ', '.join(str(pk) for pk in self.sample)
        if self.count > len(self.sample):
            return '%d (e.g. %s)' % (self.count, ids)
        return '%d (%s)' % (self.count, ids)


class TypeReport:
    """What the sweep found for one document type."""

    def __init__(self, key, missing, orphaned, deleted, stale, private):
        self.key = key
        self.missing = missing
        self.orphaned = orphaned
        # Orphans whose source row is gone from the table entirely, as opposed
        # to still being there but no longer indexable. Both are rows that
        # should not exist, but they fail for different reasons and a count
        # that merges them cannot tell you which.
        self.deleted = deleted
        self.stale = stale
        self.private = private

    @property
    def clean(self):
        return not (self.missing or self.orphaned or self.stale or self.private)

    def __str__(self):
        return ('%s: %s missing, %s orphaned (%s deleted), %s stale, '
                '%s private' % (self.key, self.missing, self.orphaned,
                                self.deleted, self.stale, self.private))


class Report:
    """What the sweep found across every document type."""

    def __init__(self, types, seconds):
        self.types = types
        self.seconds = seconds

    @property
    def clean(self):
        return all(report.clean for report in self.types)

    @property
    def private(self):
        """Total index rows pointing at members-only content."""
        return sum(report.private.count for report in self.types)

    def __str__(self):
        return '%d types in %.1fs, %s' % (
                len(self.types), self.seconds,
                'clean' if self.clean else 'DRIFT FOUND')


def drift(queryset, field='pk'):
    """
    Runs one detection query and returns its count with a bounded sample.

    The count comes first so that a clean check -- which is what every check is
    expected to be -- costs one query and fetches no rows at all.

    """
    count = queryset.count()
    if not count:
        return Drift(0)
    sample = queryset.order_by(field).values_list(field, flat=True)[:SAMPLE_SIZE]
    return Drift(count, sample)


def source_queryset(document):
    """
    The objects this document says belong in the index, stripped for counting.

    get_queryset() is the single definition of what is indexable and is what
    every check compares against, but it carries the select_related and
    prefetch_related the write path needs to build rows. None of that is wanted
    here: the joins are dead weight in an anti-join, and a prefetch would issue
    a second query to fetch objects nobody reads.

    """
    return (document.get_queryset()
            .select_related(None)
            .prefetch_related(None)
            .order_by())


def tracks_updates(model):
    """
    Whether this model records when it was last modified.

    Seven of the eight searchable models carry an indexed update_date. The
    eighth is ygroup.Post, the imported Yahoo Group archive: it is frozen
    content with no edit path in the site at all, so it has no modification
    timestamp and cannot go stale. It is checked for missing and orphaned rows
    like every other type, and simply has no staleness to check.

    """
    return any(field.name == 'update_date'
               for field in model._meta.get_fields())


def reconcile_document(document):
    """Compares one document type against its source table."""
    model = document.model
    content_type = ContentType.objects.get_for_model(model)
    rows = SearchDocument.objects.filter(content_type=content_type)
    indexable = source_queryset(document)

    # A source object the index has no row for.
    missing = drift(indexable.filter(
            ~Exists(rows.filter(object_id=OuterRef('pk')))))

    # An index row the document no longer yields. That covers a deleted object
    # and one that has left the indexable set some other way -- an unapproved
    # download, a deactivated member, a category made private -- which is the
    # same set discard_stale() removes.
    orphan_rows = rows.filter(
            ~Exists(indexable.filter(pk=OuterRef('object_id'))))
    orphaned = drift(orphan_rows, 'object_id')

    # Of those, the ones whose source row is gone from the table. This reads
    # the unfiltered manager on purpose: an object excluded by get_queryset()
    # still exists, and only the manager that still has it can say so.
    deleted = drift(orphan_rows.filter(~Exists(
            model._default_manager.filter(pk=OuterRef('object_id')))),
            'object_id')

    if tracks_updates(model):
        # The source was edited after its row was built. Judged from the index
        # side, because the row is the thing that is wrong.
        stale = drift(rows.filter(Exists(indexable.filter(
                pk=OuterRef('object_id'),
                update_date__gt=OuterRef('indexed_at')))), 'object_id')
    else:
        stale = Drift(0)

    return TypeReport(document.key, missing, orphaned, deleted, stale,
                      private_rows(document, rows))


def private_rows(document, rows):
    """
    Index rows pointing at content in a members-only forum category.

    Reported apart from the orphan count that contains it, because it is a
    different kind of failure. An orphaned row for an unapproved download is a
    search hit that 404s; an orphaned row for a private category is content
    being shown to people the category exists to keep it from. There is no
    per-user filter at query time to fall back on -- privacy is enforced by
    keeping the content out of the index -- so a single row here is a defect,
    where a hundred stale ones are a delay.

    """
    if not document.category_path:
        return Drift(0)

    private = document.model._default_manager.filter(
            **{document.category_path + '__groups__isnull': False})
    return drift(rows.filter(Exists(private.filter(pk=OuterRef('object_id')))),
                 'object_id')


def reconcile():
    """Compares every document type against its source table."""
    start = time.time()
    types = [reconcile_document(document) for document in all_documents()]
    return Report(types, time.time() - start)


def log_report(report):
    """
    Writes a sweep's findings to the search log.

    A clean sweep says so at INFO and stays one line: it is the expected result
    and will be almost every result, and a weekly line confirming the index is
    sound is worth more than silence, which is indistinguishable from the job
    not having run.

    Anything else goes to WARNING, so that grepping the log for a problem does
    not mean reading the runs that found none.

    """
    if report.clean:
        logger.info('Index reconcile: %s', report)
        return

    logger.warning('Index reconcile: %s', report)
    for type_report in report.types:
        if not type_report.clean:
            logger.warning('Index reconcile: %s', type_report)

    # Last, and on its own line, because it is the finding that is not about
    # the index being out of date.
    if report.private:
        logger.warning('Index reconcile: %d PRIVATE-CATEGORY ROWS INDEXED -- '
                       'members-only content is searchable', report.private)
