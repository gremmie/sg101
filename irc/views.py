"""views for the IRC application"""

from django.shortcuts import render_to_response
from django.template import RequestContext

from irc.models import IrcChannel

def view(request):
   nicks = IrcChannel.objects.all()
   return render_to_response('irc/view.html',
         {'nicks': nicks},
         context_instance = RequestContext(request))
