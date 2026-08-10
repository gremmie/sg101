"""
Models for the search application.

One denormalized row per searchable object: the text that gets indexed, the
values a result page renders from, and the tsvector built out of them.

One table rather than a vector per source model, because results are a single
blended list, relevance-ordered and paginated, across eight document types. A
global ordering cannot be assembled by querying eight models and merging in
Python -- page 2 would mean fetching every match from every model first.

"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.contrib.postgres.search import SearchVectorField
from django.db import IntegrityError
from django.db import models
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe


# The text search configuration. 'english' stems and drops stop words. Band and
# song names are a large share of queries and not all of them are English, so
# 'simple' is the alternative if stemming turns out to hurt more than it helps.
SEARCH_CONFIG = 'english'

# What ts_headline wraps the matched words in. Deliberately not HTML: a summary
# is plain text that may well contain angle brackets -- body_text() unescapes
# what it strips tags from, so a post reading "a < b", or one quoting markup,
# arrives here literally -- and PostgreSQL does not escape the text it wraps.
# Marking that output safe directly would publish stored input as HTML. So the
# database marks the hits with sentinels no escaping will touch, and the
# property below escapes first and inserts the markup after.
HEADLINE_START = '[[[hl]]]'
HEADLINE_STOP = '[[[/hl]]]'

# The stored vector, as a function of the row's own columns. Weights are baked
# into a tsvector, so revising them means recomputing every row -- but since the
# text they are built from lives on the row, that is one UPDATE over this table
# and never reads a source model. Normalization, by contrast, is a query-time
# argument and free to change.
SEARCH_VECTOR = (
    SearchVector('title', weight='A', config=SEARCH_CONFIG) +
    SearchVector('summary', weight='B', config=SEARCH_CONFIG) +
    SearchVector('author', weight='C', config=SEARCH_CONFIG))


class SearchDocumentManager(models.Manager):

    def index_object(self, obj, read_at=None):
        """
        Creates or updates the search document for obj, and returns it.

        read_at is when obj's field values were read from the database, and
        defaults to now. It becomes the row's indexed_at, and a row already
        built from a *later* read is left alone.

        That guard is what keeps two tasks for the same object from settling on
        the older of their two snapshots. They routinely exist: editing a
        profile saves auth.User and bio.UserProfile in one request, and both
        map to the same document, so every profile edit queues this twice. The
        worker runs several processes, so the two can interleave -- and without
        the guard, the one that read first can write last and leave the index
        holding pre-edit text that nothing would ever notice, since it stamps
        indexed_at as it goes and so looks perfectly fresh to the reconcile
        sweep.

        The bulk path in search.indexer deliberately has no such guard: a
        reindex is the repair tool, and it has to be able to overwrite a row
        however fresh that row claims to be.

        """
        # Deferred so that importing search.models does not drag in the models
        # of all seven searchable apps.
        from search.documents import document_for_model

        if read_at is None:
            read_at = timezone.now()

        values = document_for_model(obj._meta.model).build(obj)
        values['indexed_at'] = read_at

        content_type = ContentType.objects.get_for_model(obj)
        rows = self.filter(content_type=content_type, object_id=obj.pk)

        if not rows.filter(indexed_at__lt=read_at).update(**values):
            if rows.exists():
                # A fresher read got here first; its row stands.
                return rows.first()
            try:
                # atomic() so that losing the insert race leaves a usable
                # transaction behind rather than an aborted one.
                with transaction.atomic():
                    self.create(content_type=content_type, object_id=obj.pk,
                                **values)
            except IntegrityError:
                # Another task created the row between the update and here,
                # which means it read at least as recently as we did.
                return rows.first()

        rows.update(search_vector=SEARCH_VECTOR)
        return rows.first()


class SearchDocument(models.Model):
    """A searchable document: one row per indexed source object."""

    # db_index=False: the unique constraint below already indexes this column
    # as its leading one, and a second btree over 490k rows earns nothing.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     db_index=False)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # The indexed text, one field per weight band. title is a TextField because
    # two of the eight are composed -- a profile's is "username (Full Name)" --
    # and overflowing a varchar is a DataError on PostgreSQL.
    title = models.TextField()
    summary = models.TextField(blank=True)
    author = models.CharField(max_length=255, blank=True)

    # Denormalized so a result page renders from this table alone, rather than
    # fanning out across eight source models to display ten results.
    url = models.CharField(max_length=255)
    date = models.DateTimeField()

    # When this row was last rebuilt. Compared against the source's update_date
    # by the reconcile sweep, which is the only thing that reads it.
    indexed_at = models.DateTimeField()

    search_vector = SearchVectorField(null=True)

    objects = SearchDocumentManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['content_type', 'object_id'],
                                    name='search_document_unique_source'),
        ]
        # The GIN index is the one that matters; the unique constraint's btree
        # doubles as the index for filtering by content_type, that being its
        # leading column. Nothing indexes date: results order by rank first,
        # which is a computed expression, so the sort runs over the matched set
        # regardless. indexed_at stays unindexed until the reconcile sweep
        # shows it needs to be.
        indexes = [GinIndex(fields=['search_vector'])]

    def __str__(self):
        return self.title

    @property
    def result_label(self):
        """What this document's type is called on a result row."""
        from search.documents import document_for_model

        return document_for_model(self.content_type.model_class()).result_label

    @property
    def highlighted(self):
        """
        The snippet for a result row, with the matched words marked up.

        Reads the `headline` annotation search.query adds, so it is only
        available on rows that came from a search.

        """
        escaped = escape(self.headline)
        return mark_safe(
                escaped.replace(escape(HEADLINE_START),
                                '<span class="highlight">')
                       .replace(escape(HEADLINE_STOP), '</span>'))
