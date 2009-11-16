"""
Views for the core application. These are mainly shared, common views
used by multiple applications.
"""
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

@login_required
@require_GET
def markdown_help(request):
    """
    This view provides the Markdown help cheat sheet. It is expected
    to be called via AJAX.
    """
    return render_to_response('core/markdown_help.html')
