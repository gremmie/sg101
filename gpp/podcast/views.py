"""Views for the podcast application"""

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404

from podcast.models import Channel
from podcast.models import Item


def index(request):
   try:
      channel = Channel.objects.get(pk=1)
   except Channel.DoesNotExist:
      channel = None

   return render_to_response('podcast/index.html', {
      'channel': channel, 
      },
      context_instance = RequestContext(request))


def detail(request, id):
   podcast = get_object_or_404(Item, pk = id)
   return render_to_response('podcast/detail.html', {
      'channel': podcast.channel,
      'podcast': podcast, 
      },
      context_instance = RequestContext(request))
   

def feed(request):
   try:
      channel = Channel.objects.get(pk=1)
   except Channel.DoesNotExist:
      channel = None
   return render_to_response('podcast/feed.xml', {
      'channel': channel, 
      },
      context_instance = RequestContext(request))
