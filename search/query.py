"""
Running a search: the query, the ranking, and the snippets.

The read path, as search.indexer is the write path. The view supplies a query
string and the types to search; everything about how that becomes ranked rows
lives here.

"""
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchHeadline
from django.contrib.postgres.search import SearchQuery
from django.contrib.postgres.search import SearchRank
from django.db.models import F
from django.db.models import Value

from search.documents import document_for_key
from search.models import HEADLINE_START
from search.models import HEADLINE_STOP
from search.models import SEARCH_CONFIG
from search.models import SearchDocument


# How much of the summary a result row shows, matching the 200 characters the
# old template's {% highlight %} tag was told to produce.
HEADLINE_MAX_WORDS = 35
HEADLINE_MIN_WORDS = 15


def positive_terms(query):
    """
    Returns query with its excluded terms removed.

    Ranking needs this because ts_rank collapses to a constant the moment a
    tsquery contains a negated term: every row matching `reverb -fender` scores
    6.3e-21, identically, so ordering by rank silently degenerates to ordering
    by the date tiebreak alone. Filtering keeps the full query -- exclusion has
    to actually exclude -- and only the ranking expression is built from what
    is left.

    Websearch's exclusion syntax is a leading `-` on either a bare word or a
    quoted phrase, so dropping those tokens is enough; anything else, including
    unbalanced quotes, passes through for websearch_to_tsquery to interpret,
    which it does without ever raising.

    """
    terms = []
    rest = query
    while rest:
        rest = rest.lstrip()
        if not rest:
            break
        excluded = rest.startswith('-')
        token = rest[1:] if excluded else rest

        if token.startswith('"'):
            end = token.find('"', 1)
            # An unclosed quote runs to the end of the string, which is how
            # websearch_to_tsquery reads it too.
            end = len(token) if end == -1 else end + 1
        else:
            end = token.find(' ')
            end = len(token) if end == -1 else end

        if not excluded:
            terms.append(token[:end])
        rest = token[end:]

    return ' '.join(terms)


def search_documents(query, keys):
    """
    Returns the search documents matching query, best first.

    keys names the types to search, as the search form's `app_label.model`
    values. Results are ordered by relevance and then newest-first among equal
    scores -- the old search ordered by date alone, so the ranking is a
    deliberate change rather than restored behavior.

    """
    tsquery = SearchQuery(query, search_type='websearch', config=SEARCH_CONFIG)
    ranked = SearchQuery(positive_terms(query), search_type='websearch',
                         config=SEARCH_CONFIG)

    documents = [document_for_key(key) for key in keys]
    content_types = ContentType.objects.get_for_models(
            *[document.model for document in documents])

    return (SearchDocument.objects
            # select_related because every result row names its own type, and
            # the label for that comes through content_type.
            .select_related('content_type')
            .filter(content_type__in=content_types.values())
            .filter(search_vector=tsquery)
            .annotate(
                # normalization=1 divides by 1 + log(document length), so a
                # 900-word forum post does not outrank a tight news headline on
                # bulk alone. It is a query-time argument, unlike the A/B/C
                # weights baked into the stored vector, and so is cheap to
                # revise.
                rank=SearchRank(F('search_vector'), ranked,
                                normalization=Value(1)),
                headline=SearchHeadline('summary', ranked,
                                        config=SEARCH_CONFIG,
                                        start_sel=HEADLINE_START,
                                        stop_sel=HEADLINE_STOP,
                                        max_words=HEADLINE_MAX_WORDS,
                                        min_words=HEADLINE_MIN_WORDS))
            .order_by('-rank', '-date'))
