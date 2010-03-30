"""
Views for the core application. These are mainly shared, common views
used by multiple applications.
"""
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
import django.utils.simplejson as json


@login_required
@require_GET
def markdown_help(request):
    """
    This view provides the Markdown help cheat sheet. It is expected
    to be called via AJAX.
    """
    return render_to_response('core/markdown_help.html')


def ajax_users(request):
    """
    If the user is authenticated, return a JSON array of strings of usernames 
    whose names start with the 'q' GET parameter, limited by the 'limit' GET 
    parameter. Only active usernames are returned.
    If the user is not authenticated, return an empty array.
    """
    q = request.GET.get('q', None)
    if q is None or not request.user.is_authenticated():
        return HttpResponse(json.dumps([]), content_type='application/json')

    limit = int(request.GET.get('limit', 10))
    users = User.objects.filter(is_active=True, 
            username__istartswith=q).values_list('username', flat=True)[:limit]
    return HttpResponse(json.dumps(list(users)), content_type='application/json')
