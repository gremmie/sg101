import os
import sys

OFFLINE = False

sys.path.append('/home/var/django-sites/sg101')
sys.path.append('/home/var/django-sites/sg101/3rdparty')
sys.path.append('/home/var/django-sites/sg101/sg101-trunk')
sys.path.append('/home/var/django-sites/sg101/sg101-trunk/gpp')

os.environ['PYTHON_EGG_CACHE'] = '/home/var/django-sites/sg101/eggs/'


def offline_handler(environ, start_response):
    wsgi_dir = os.path.dirname(__file__)
    sys.path.append(wsgi_dir)

    offline_file = os.path.join(wsgi_dir, '..', 'templates', 'offline.html')
    if os.path.exists(offline_file):
        response_headers = [('Content-type','text/html')]
        response = open(offline_file).read()
    else:
        response_headers = [('Content-type','text/plain')]
        response = 'SG101 website maintenance in progress; please check back soon.'
 
    if environ['REQUEST_METHOD'] == 'GET':
        status = '503 Service Unavailable'
    else:
        status = '405 Method Not Allowed'
    start_response(status, response_headers)
    return [response]


if not OFFLINE:
   os.environ['DJANGO_SETTINGS_MODULE'] = 'gpp.settings.production'
   import django.core.handlers.wsgi
   application = django.core.handlers.wsgi.WSGIHandler()
else:
   application = offline_handler

