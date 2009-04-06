"""views for the legal application"""

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from legal.models import Policy

def view(request, policy_name):
   policy = get_object_or_404(Policy, policy_type = policy_name)
   return render_to_response('legal/view.html',
         {'policy' : policy},
         context_instance = RequestContext(request))
