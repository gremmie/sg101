"""Views for the antispam application."""

from django.shortcuts import render_to_response
from django.template import RequestContext

import bio.models


def suspended(request):
    """This view checks the user's status for suspension and displays an
    appropriate message.
    """
    is_active = request.user.is_active

    return render_to_response('antispam/suspended.html', {
        'is_active': is_active,
        }, 
        context_instance = RequestContext(request))
