"""Common middleware for the entire project."""
from django.contrib.auth import logout

class InactiveUserMiddleware(object):
    """
    This middleware ensures users with is_active set to False get their
    session destroyed and are treated as logged out.
    This middleware should come after the 'django.contrib.auth.middleware.
    AuthenticationMiddleware' in settings.py.
    Idea taken from: http://djangosnippets.org/snippets/1105/
    """

    def process_request(self, request):
        if request.user.is_authenticated() and not request.user.is_active:
            logout(request)

