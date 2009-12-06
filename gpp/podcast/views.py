"""Views for the podcast application"""
import os.path
from urlparse import urlparse

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404

from podcast.models import Channel
from podcast.models import Item


def get_ext_from_url(url):
    """
    This function returns the extension part of the path from the given
    url.
    """
    return os.path.splitext(urlparse(url).path)[1]


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
   podcast = get_object_or_404(Item.objects.select_related(), pk = id)

   ext = get_ext_from_url(podcast.enclosure_url)
   alt_ext = None
   if podcast.alt_enclosure_url:
      alt_ext = get_ext_from_url(podcast.alt_enclosure_url)

   return render_to_response('podcast/detail.html', {
      'channel': podcast.channel,
      'podcast': podcast, 
      'ext': ext,
      'alt_ext': alt_ext,
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
