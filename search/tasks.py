"""
Celery tasks for the search application.

Every write to the index goes through here. Nothing indexes inline, and there
is no synchronous path to fall back to: indexing a post costs milliseconds and
nobody would feel it, but a bug in building a vector would then break posting
itself. Through a task the post succeeds, the index lags, and the remedy is a
reindex rather than an outage.

The signal handlers in search.receivers are what queue these, always on commit.

"""

import logging

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db import InterfaceError
from django.db import OperationalError
from django.utils import timezone

from forums.models import Post

from search.documents import all_documents
from search.documents import document_for_model
from search.indexer import discard_stale
from search.indexer import index_queryset
from search.models import SearchDocument
from search.reconcile import log_report
from search.reconcile import reconcile


# The search log, by name and not by module, exactly as search/reconcile.py
# does and for the same reason: celery's get_task_logger() reparents the logger
# it returns onto celery.task, which carries these lines away from the handler
# they are meant for and into the worker's log instead.
logger = logging.getLogger('search')

# A dropped connection or a database restart should cost a document a few
# seconds, not remove it from the index until someone notices and reindexes.
# Only the transient errors retry; a bug in building a vector raises whatever
# it raises and gets logged, since repeating it would only fail again.
RETRY = {
    'autoretry_for': (OperationalError, InterfaceError),
    'retry_backoff': True,
    'retry_jitter': True,
    'retry_kwargs': {'max_retries': 5},
}


@shared_task(**RETRY)
def reindex_document(content_type_id, object_id):
    """
    Writes the index row for one object, or removes it if it has no place.

    The object is looked up through its document's own queryset, which is what
    makes one task enough for every reason a row might need to go away. Deleted
    between queueing and running, its category made private, a link unpublished,
    a member deactivated: in each case the queryset no longer yields it and the
    row goes. None of those is an error.

    """
    document = document_for_content_type(content_type_id)
    if document is None:
        return

    # Taken before the read, not after: it is how fresh this task's data is,
    # and index_object compares it against what the row already holds so that
    # a task which read early cannot overwrite one that read late.
    read_at = timezone.now()

    obj = document.get_queryset().filter(pk=object_id).first()
    if obj is None:
        removed = delete_row(content_type_id, object_id)
        if removed:
            logger.info("removed %s %s from the index (no longer indexable)",
                        document.model._meta.label_lower, object_id)
        return

    SearchDocument.objects.index_object(obj, read_at=read_at)


@shared_task(**RETRY)
def remove_document(content_type_id, object_id):
    """
    Removes one object's index row.

    Deletes queue this rather than reindex_document because the object is
    already gone by the time the task runs: there is nothing to look up and
    no ambiguity about what to do.

    """
    delete_row(content_type_id, object_id)


@shared_task(**RETRY)
def reindex_category(category_id):
    """
    Rebuilds the index for one forum category's topics and posts.

    Queued when a category's groups change, which is how a category becomes
    private or public again. The task does not need to know which way it went:
    it indexes whatever the documents still yield for the category and drops
    the rows of everything they no longer do, so gaining a group empties the
    category out of the index and losing one fills it back in.

    """
    for document in all_documents():
        if not document.category_path:
            continue

        scope = {document.category_path: category_id}
        indexed = index_queryset(document,
                                 document.get_queryset().filter(**scope))
        removed = discard_stale(document, scope=scope)
        logger.info("category %s: %s %d indexed, %d removed", category_id,
                    document.model._meta.label_lower, indexed, removed)


@shared_task(**RETRY)
def reindex_topic_posts(topic_id):
    """
    Rebuilds the index rows for one topic's posts.

    Queued when a topic moves or is renamed. Each post is indexed under its
    topic's name and governed by its category's privacy, and neither change
    saves the posts. As with a category, the posts the document no longer
    yields -- moved into a private category -- have their rows dropped.

    """
    document = document_for_model(Post)
    scope = {'topic': topic_id}
    indexed = index_queryset(document, document.get_queryset().filter(**scope))
    removed = discard_stale(document, scope=scope)
    logger.info("topic %s: %d posts indexed, %d removed", topic_id, indexed,
                removed)


@shared_task(**RETRY)
def reconcile_index():
    """
    Compares the index against its source tables and reports what it finds.

    Runs weekly from Beat. Everything above keeps the index current from site
    activity, and none of it can say so: a worker that was down, a task that was
    lost, a flushed broker or a snapshot reloaded underneath the site all leave
    an index that is quietly wrong and looks exactly like one that is right.
    This is the job that breaks that silence.

    It reports and repairs nothing, deliberately -- see search.reconcile. The
    remedy for anything it finds is reindex_search, run by hand.

    """
    log_report(reconcile())


def document_for_content_type(content_type_id):
    """
    Returns the document for a content type id, or None if there is not one.

    A content type that is no longer searchable is the ordinary consequence of
    a document being unregistered while tasks for it were still queued, and the
    command's own sweep clears the rows it left behind.

    """
    try:
        model = ContentType.objects.get_for_id(content_type_id).model_class()
    except ContentType.DoesNotExist:
        model = None

    if model is None:
        logger.warning("no model for content type %s; skipping",
                       content_type_id)
        return None

    try:
        return document_for_model(model)
    except KeyError:
        logger.warning("%s is not searchable; skipping",
                       model._meta.label_lower)
        return None


def delete_row(content_type_id, object_id):
    """Deletes one index row if it exists; returns how many went."""
    count, _ = SearchDocument.objects.filter(
            content_type_id=content_type_id, object_id=object_id).delete()
    return count
