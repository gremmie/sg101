"""
This file contains views that don't belong to any specific application.
In particular, the home page view.
"""
from django.shortcuts import render_to_response
from django.template import RequestContext


def home(request):
    """
    The home page view of the site.
    """
    return render_to_response('home.html', {
        }, 
        context_instance = RequestContext(request))
