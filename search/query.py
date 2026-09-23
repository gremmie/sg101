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
from django.db.models import Count
from django.db.models import F
from django.db.models import Value

from search.documents import all_documents
from search.documents import document_for_key
from search.models import HEADLINE_START
from search.models import HEADLINE_STOP
from search.models import SEARCH_CONFIG
from search.models import SearchDocument


# How much of the summary a result row shows, matching the 200 characters the
# old template's {% highlight %} tag was told to produce.
HEADLINE_MAX_WORDS = 35
HEADLINE_MIN_WORDS = 15

# Names the site spells more than one way, each group written as members type
# it. The index holds words as written, so without this neither spelling finds
# the other -- and the site's signature tune is split between two.
#
# Extending a group is only a matter of adding to it -- nothing is reindexed,
# because the rewrite happens to the query. What it cannot bridge is a form
# whose words the parser drops: "wipe out" indexes as just 'wipe', since 'out'
# is an English stop word, so there is nothing to rewrite from.
SPELLINGS = [
    ['misirlou', 'miserlou', 'miserlu'],
    ['straitjackets', 'straightjackets'],
    ['bel-airs', 'belairs', 'bel airs'],
]


class SpellingSearchQuery(SearchQuery):
    """
    A websearch query in which any spelling of a SPELLINGS name finds them all.

    ts_rewrite works on the parsed tsquery rather than the typed string, so a
    spelling is bridged wherever it sits: alone, inside a quoted phrase, or
    excluded, where excluding one spelling excludes every one.

    Each form is a target twice over, because typed two words it parses as an
    AND of both and quoted as a phrase. Either way it is replaced by itself OR
    the whole group, never by the group alone -- so a rewrite only ever adds
    matches, and a query still finds everything it found before.

    """
    def as_sql(self, compiler, connection, **kwargs):
        sql, params = super().as_sql(compiler, connection, **kwargs)
        for group in SPELLINGS:
            either = ' || '.join(['phraseto_tsquery(%s, %s)'] * len(group))
            either_params = [value for form in group
                             for value in (SEARCH_CONFIG, form)]
            for form in group:
                for parse in ('plainto_tsquery', 'phraseto_tsquery'):
                    target = f'{parse}(%s, %s)'
                    sql = f'ts_rewrite({sql}, {target}, {target} || {either})'
                    params = [*params, SEARCH_CONFIG, form, SEARCH_CONFIG,
                              form, *either_params]
        return sql, params


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


def matching_documents(query):
    """
    Returns every document matching query, of any type and in no order.

    The match set, separated from what is done with it. The result page filters
    this by type, ranks it and orders it; the per-type counts group the same set
    without filtering, because a count has to say how many results checking a
    box *would* give, which the box being unchecked must not change.

    """
    tsquery = SpellingSearchQuery(query, search_type='websearch',
                                  config=SEARCH_CONFIG)
    return SearchDocument.objects.filter(search_vector=tsquery)


def content_types_for(documents):
    """Returns the ContentTypes of these documents, in their order."""
    content_types = ContentType.objects.get_for_models(
            *[document.model for document in documents])
    return [content_types[document.model] for document in documents]


def type_counts(query):
    """
    Returns how many documents of each type match query, in registry order.

    Keyed by the form's `app_label.model` values, so the caller can pair each
    count with the checkbox that selects it, and carrying a zero for the types
    nothing matched -- a type that vanishes from the list when it has no hits
    tells a member less than one that says nothing is there.

    """
    documents = all_documents()
    keys = {content_type.pk: document.key for document, content_type
            in zip(documents, content_types_for(documents))}

    counts = {document.key: 0 for document in documents}
    rows = (matching_documents(query)
            .filter(content_type__in=keys)
            # order_by() clears any ordering before the aggregate, and is not
            # optional. GROUP BY takes the ordering columns with it, so an
            # ordered queryset grouped this way puts rank and date into the
            # grouping, every row becomes its own group, and every count comes
            # back as 1 -- a wrong answer that looks like a plausible one.
            .order_by()
            # Grouped by content_type rather than content_type__model, because
            # forums.Post and ygroup.Post are both named "post" and grouping on
            # the name silently merges them into a single count.
            .values('content_type')
            .annotate(total=Count('pk')))

    for row in rows:
        counts[keys[row['content_type']]] = row['total']
    return counts


def search_documents(query, keys):
    """
    Returns the search documents matching query, best first.

    keys names the types to search, as the search form's `app_label.model`
    values. Results are ordered by relevance and then newest-first among equal
    scores -- the old search ordered by date alone, so the ranking is a
    deliberate change rather than restored behavior.

    """
    ranked = SpellingSearchQuery(positive_terms(query), search_type='websearch',
                                 config=SEARCH_CONFIG)

    documents = [document_for_key(key) for key in keys]

    return (matching_documents(query)
            # select_related because every result row names its own type, and
            # the label for that comes through content_type.
            .select_related('content_type')
            .filter(content_type__in=content_types_for(documents))
            .annotate(
                # normalization=1 divides by 1 + log(document length). What that
                # buys is a tiebreak: ts_rank alone scores every document whose
                # title matches the query almost identically -- eight rows
                # titled "Sundazed Music" all come back 0.9910322 -- so without
                # it the ordering of a large result set collapses onto the date.
                # The cost is that the tiebreak is brevity, and topics carry no
                # summary at all, so they win it structurally; weblinks and
                # downloads place well below their worth on broad queries. That
                # is a volume problem between types rather than a ranking error
                # within one, and the per-type result counts are what address
                # it. It is a query-time argument, unlike the A/B/C weights
                # baked into the stored vector, and so is cheap to revise.
                rank=SearchRank(F('search_vector'), ranked,
                                normalization=Value(1)),
                headline=SearchHeadline('summary', ranked,
                                        config=SEARCH_CONFIG,
                                        start_sel=HEADLINE_START,
                                        stop_sel=HEADLINE_STOP,
                                        max_words=HEADLINE_MAX_WORDS,
                                        min_words=HEADLINE_MIN_WORDS))
            .order_by('-rank', '-date'))
