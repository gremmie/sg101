"""Views for the search application."""
import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import InvalidPage
from django.http import Http404
from django.shortcuts import render

from core.functions import get_ip
from core.functions import get_page
from core.paginator import DiggPaginator
from search.forms import SearchForm
from search.query import search_documents
from search.query import type_counts


RESULTS_PER_PAGE = 20

# Its own logger, writing its own file, so that what members search for stays
# readable without sg101.log's traffic around it.
logger = logging.getLogger('search')


class CountedPaginator(DiggPaginator):
    """
    A paginator told its total rather than left to go and count.

    The per-type counts sum to the number of results, so the COUNT(*) the
    paginator would issue is a second pass over the set the counts have already
    walked. Handing it the total keeps a search at two queries instead of three.

    Paginator.count is a cached_property, which is a non-data descriptor, so
    assigning the instance attribute is what shadows it.

    """
    def __init__(self, object_list, per_page, count, **kwargs):
        super().__init__(object_list, per_page, **kwargs)
        self.count = count


@login_required
def search(request):
    """
    The search page.

    Login is required because bots were hammering this hard enough to hurt the
    site, one of them walking search input looking for SQL injection. That is
    also why nothing here reports a malformed query back to the user:
    websearch_to_tsquery never raises, so there is no parse error to leak.

    """
    form = SearchForm(request.GET) if 'q' in request.GET else SearchForm()
    the_page = None

    if form.is_bound and form.is_valid():
        query = form.cleaned_data['q']
        keys = form.cleaned_data['models']

        logger.info('Search: %s in %s by %s [%s]', query, keys,
                    request.user.username, get_ip(request))

        # Counted over the query alone, with no type filter, so that each
        # number answers "how many would checking this box give me" rather than
        # changing according to what is checked now. Narrowing to one type would
        # otherwise zero every other count and take away the thing that makes
        # narrowing an informed choice.
        counts = type_counts(query)
        form.show_counts(counts)

        paginator = CountedPaginator(search_documents(query, keys),
                                     RESULTS_PER_PAGE,
                                     sum(counts[key] for key in keys),
                                     body=5, tail=2, margin=3, padding=2)
        try:
            the_page = paginator.page(get_page(request.GET))
        except InvalidPage:
            raise Http404

    return render(request, 'search/search.html', {
        'form': form,
        'page': the_page,
        'V3_DESIGN': True,
        })


# The only type this endpoint searches. It is not a parameter: the feature is
# a duplicate-topic check, and there is no intention of offering quick searches
# over the other seven document types.
TOPIC_KEYS = ['forums.topic']


@login_required
def search_topics(request):
    """
    The forums' duplicate-topic check, returning an HTML fragment.

    Not a general-purpose endpoint, and deliberately not built to become one. A
    member writing a new topic clicks the "Quick Search" button beside the title
    field, `forums/static/js/forums.js` sends the title here, and the matches
    render inline so they can see whether their question already exists.

    That JavaScript requests `/search/topics/` literally rather than reversing
    this route, so the path is part of the contract even though the route name
    is not.

    """
    form = SearchForm(request.GET)
    the_page = None

    if form.is_valid():
        # Logged like any deliberate search, but marked, because it answers a
        # different question: not what a member wanted to find, but what they
        # were about to post.
        logger.info('Forum topics quick search: %s by %s [%s]',
                    form.cleaned_data['q'], request.user.username,
                    get_ip(request))

        paginator = DiggPaginator(
                search_documents(form.cleaned_data['q'], TOPIC_KEYS),
                RESULTS_PER_PAGE, body=5, tail=2, margin=3, padding=2)
        try:
            the_page = paginator.page(1)
        except InvalidPage:
            the_page = None

    return render(request, 'search/search_topics.html', {
        'query': form.data.get('q', ''),
        'page': the_page,
        })
