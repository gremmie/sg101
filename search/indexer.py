"""
The batched write path into the search index.

One object at a time is SearchDocument.objects.index_object(); this module is
what writes many at once, and it is shared rather than duplicated -- the
reindex_search command rebuilds whole document types through it, and the task
that reacts to a forum category's privacy changing rebuilds one category's
worth through the same code.

A batch is one transaction and a fixed four queries, regardless of its size:
read the rows that already exist, create the ones that do not, update the ones
that do, then have PostgreSQL build the vectors in place. The vector is a
function of the columns just written, so it never travels over the wire.

"""

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import prefetch_related_objects
from django.utils import timezone

from search.models import SEARCH_VECTOR
from search.models import SearchDocument


# The columns build() supplies, in the order bulk_update should write them.
DOCUMENT_FIELDS = ['title', 'summary', 'author', 'url', 'date', 'indexed_at']

# Rows per batch: one transaction, one round of queries, one progress step.
BATCH_SIZE = 1000


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


def index_batch(document, content_type, batch):
    """Creates or updates the index rows for one batch of objects."""
    # iterator() ignores prefetch_related, so the batch prefetches its own.
    if document.prefetch:
        prefetch_related_objects(batch, *document.prefetch)

    object_ids = [obj.pk for obj in batch]
    rows = SearchDocument.objects.filter(content_type=content_type,
                                         object_id__in=object_ids)
    existing = dict(rows.values_list('object_id', 'pk'))

    now = timezone.now()
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


def index_queryset(document, queryset, batch_size=BATCH_SIZE, on_progress=None):
    """
    Writes an index row for every object in queryset; returns how many.

    The queryset is the caller's to narrow -- a whole document type for a full
    rebuild, one category's topics for a privacy change -- but it must be one
    the document's own get_queryset() produced, so that what gets indexed has
    only ever had one definition.

    """
    content_type = ContentType.objects.get_for_model(document.model)

    indexed = 0
    # iterator() streams from a server-side cursor, so the source table is
    # never held in memory. Each batch is then its own transaction: a failure
    # at row 400,000 leaves the first 399,999 written.
    #
    # order_by() drops the model's Meta ordering: a sweep does not care what
    # order it walks the table in, and sorting 463k rows to ignore the result
    # is pure cost.
    for batch in batched(queryset.order_by().iterator(chunk_size=batch_size),
                         batch_size):
        with transaction.atomic():
            index_batch(document, content_type, batch)
        indexed += len(batch)
        if on_progress is not None:
            on_progress(indexed)

    return indexed


def discard_stale(document, scope=None):
    """
    Deletes this type's rows whose object the document no longer yields.

    That covers a deleted object and an object that has left the indexable set
    some other way -- a forum category being made private takes its topics and
    posts out of the queryset, and this is what takes them out of the index.

    scope limits the sweep to the objects matching those lookups, so a caller
    working on one category does not have to consider the whole type. Without
    it every row of the type is a candidate.

    """
    content_type = ContentType.objects.get_for_model(document.model)
    indexable = document.get_queryset()
    rows = SearchDocument.objects.filter(content_type=content_type)

    if scope is not None:
        indexable = indexable.filter(**scope)
        # Confine the sweep to rows whose object matches scope. This reads the
        # model's unfiltered manager on purpose: the objects that just became
        # unindexable are exactly the ones missing from the document queryset,
        # so they can only be found through the manager that still has them.
        rows = rows.filter(object_id__in=document.model._default_manager.filter(
            **scope).values('pk'))

    count, _ = rows.exclude(object_id__in=indexable.values('pk')).delete()
    return count
