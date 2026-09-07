"""
Bulk tag edits for the news models.

Renaming and merging are the same operation -- replace one tag with another
everywhere it appears -- differing only in what they refuse. What matters here
is how the write is made: not through `Story.save()`.

`StoryBase.save()` re-renders `short_text` from `short_markup`, and measured
against the production archive that changes the visible text of 14 stories,
where Markdown's emphasis conformance fix turns what is stored as bold into
literal asterisks. Editing a tag must not rewrite a body. So these use
`bulk_update`, which writes named columns and nothing else -- and then have to do
by hand the two things `save()` would have done: move `update_date`, and queue
the search reindex.

`update_date` is not cosmetic here. `reconcile_search` finds a stale index row by
comparing it against `indexed_at`, so leaving it alone would hide this change
from the one sweep that exists to catch a reindex that did not happen.

"""
from django.utils import timezone

from news.models import PendingStory, Story
from search.documents import all_documents
from search.receivers import queue
from search.tasks import reindex_document


# Both carry tags; only one of them is searchable.
TAGGED_MODELS = (Story, PendingStory)


def _searchable(model):
    return any(document.model is model for document in all_documents())


def _replace(tags, old, new):
    """Swap `old` for `new`, keeping the order and dropping a duplicate.

    Order matters because the story page renders tags in the order they are
    stored, and a story carrying both tags in a merge would otherwise end up
    with the destination twice.
    """
    seen = set()
    replaced = []
    for tag in tags:
        tag = new if tag == old else tag
        if tag not in seen:
            seen.add(tag)
            replaced.append(tag)
    return replaced


def tag_in_use(tag):
    """Is any story, published or pending, carrying this tag?"""
    return any(model.objects.filter(tags__contains=[tag]).exists()
               for model in TAGGED_MODELS)


def retag(old, new, dry_run=False):
    """Replace tag `old` with `new` everywhere. Returns a count per model."""
    counts = {}
    now = timezone.now()

    for model in TAGGED_MODELS:
        rows = list(model.objects.filter(tags__contains=[old]))
        counts[model] = len(rows)
        if dry_run or not rows:
            continue

        for row in rows:
            row.tags = _replace(row.tags, old, new)
            row.update_date = now
        model.objects.bulk_update(rows, ['tags', 'update_date'])

        # bulk_update fires no post_save, so the reindex receivers never see
        # this. Queued the same way they would have: on commit, by content type.
        if _searchable(model):
            for row in rows:
                queue(reindex_document, model, row.pk)

    return counts
