"""Custom views for searching."""

from haystack.views import SearchView


class UserSearchView(SearchView):
    """This class passes the user making the search as an __init__ argument to
    the search form as the keyword argument 'user'.

    """
    def build_form(self, form_kwargs=None):
        """Pass the request.user object to the form's constructor."""
        if not form_kwargs:
            form_kwargs = {}
        if 'user' not in form_kwargs:
            form_kwargs['user'] = self.request.user
        return super(UserSearchView, self).build_form(form_kwargs)
