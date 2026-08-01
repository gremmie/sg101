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


RESULTS_PER_PAGE = 20

# Its own logger, writing its own file, so that what members search for stays
# readable without sg101.log's traffic around it.
logger = logging.getLogger('search')


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

        paginator = DiggPaginator(search_documents(query, keys),
                                  RESULTS_PER_PAGE, body=5, tail=2, margin=3,
                                  padding=2)
        try:
            the_page = paginator.page(get_page(request.GET))
        except InvalidPage:
            raise Http404

    return render(request, 'search/search.html', {
        'form': form,
        'page': the_page,
        'V3_DESIGN': True,
        })
