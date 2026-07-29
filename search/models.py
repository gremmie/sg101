"""
Models for the search application.

One denormalized row per searchable object: the text that gets indexed, the
values a result page renders from, and the tsvector built out of them.

One table rather than a vector per source model, because results are a single
blended list, relevance-ordered and paginated, across eight document types. A
global ordering cannot be assembled by querying eight models and merging in
Python -- page 2 would mean fetching every match from every model first.

"""
import datetime

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.contrib.postgres.search import SearchVectorField
from django.db import models


# The text search configuration. 'english' stems and drops stop words. Band and
# song names are a large share of queries and not all of them are English, so
# 'simple' is the alternative if stemming turns out to hurt more than it helps.
SEARCH_CONFIG = 'english'

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

    def index_object(self, obj):
        """
        Creates or updates the search document for obj, and returns it.

        Two statements: the column values, then the vector built from them.

        """
        # Deferred so that importing search.models does not drag in the models
        # of all seven searchable apps.
        from search.documents import document_for_model

        values = document_for_model(obj._meta.model).build(obj)
        values['indexed_at'] = datetime.datetime.now()

        doc, _ = self.update_or_create(
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.pk,
                defaults=values)
        self.filter(pk=doc.pk).update(search_vector=SEARCH_VECTOR)
        return doc


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
