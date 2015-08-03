"""Custom views for searching."""
import logging

from django.shortcuts import render_to_response
from haystack.views import SearchView
from xapian import QueryParserError

logger = logging.getLogger(__name__)

class UserSearchView(SearchView):
    """This class passes the user making the search as an __init__ argument to
    the search form as the keyword argument 'user'.

    """
    query_parser_error = False

    def build_form(self, form_kwargs=None):
        """Pass the request.user object to the form's constructor."""
        if not form_kwargs:
            form_kwargs = {}
        if 'user' not in form_kwargs:
            form_kwargs['user'] = self.request.user
        return super(UserSearchView, self).build_form(form_kwargs)

    # This nonsense is because Xapian can raise QueryParserError when evaluating
    # the query. This was triggered by some sh*t-bag looking for SQL injection
    # vulnerabilities.
    # If QueryParserError is raised, just drive on and set a flag in the context
    # (via extra_context()) so that an error is rendered on the template instead
    # of a 500 error.

    def create_response(self):
        try:
            return super(UserSearchView, self).create_response()
        except QueryParserError:
            self.query_parser_error = True

        logger.warning("QueryParserError triggered from user search input")

        context = {
            'query': self.query,
            'form': self.form,
            'page': None,
            'paginator': None,
            'suggestion': None,
        }

        context.update(self.extra_context())
        return render_to_response(self.template, context,
                                  context_instance=self.context_class(self.request))

    def extra_context(self):
        return {
            'query_parser_error': self.query_parser_error,
        }
