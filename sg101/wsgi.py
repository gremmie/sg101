"""
WSGI entry point, for the server that runs the site in production.

gunicorn imports this as `sg101.wsgi:application`. The development server does
not use it at all -- runserver builds its own handler -- so nothing here is
exercised by `manage.py runserver` or by the test suite.

No default settings module on purpose. manage.py and celery.py both default to
the development settings, which is the right convenience for a person at a
terminal; the same default here would mean a server whose environment lost the
variable comes up with DEBUG on, ALLOWED_HOSTS wide open and the debug toolbar
installed, serving tracebacks to the internet. Failing to start is the better
outcome, and every way this module is launched -- compose, a shell, a deploy --
sets the variable explicitly.
"""
from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
