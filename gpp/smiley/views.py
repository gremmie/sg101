"""
Views for the Smiley application.
"""
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from smiley.models import Smiley

@login_required
@require_GET
def farm(request, extra=False):
    return render_to_response('smiley/smiley_farm.html', {
        'smilies': Smiley.objects.get_smilies(extra),
        },
        context_instance = RequestContext(request))

