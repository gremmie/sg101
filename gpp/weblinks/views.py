"""
Views for the weblinks application.
"""

import datetime
import random
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import auth
from django.core.paginator import InvalidPage
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.views.decorators.http import require_POST

from core.paginator import DiggPaginator
from core.functions import email_admins
from weblinks.models import Category
from weblinks.models import Link
from weblinks.models import FlaggedLink
from weblinks.forms import SearchForm
from weblinks.forms import AddLinkForm

#######################################################################

LINKS_PER_PAGE = 10

def create_paginator(links):
   return DiggPaginator(links, LINKS_PER_PAGE, body=5, tail=3, margin=3, padding=2)

#######################################################################

def link_index(request):
   categories = Category.objects.all()
   total_links = Link.public_objects.all().count()
   return render_to_response('weblinks/index.html', {
      'categories': categories, 
      'total_links': total_links,
      },
      context_instance = RequestContext(request))

#######################################################################

def new_links(request):
   links = Link.public_objects.order_by('-date_added')[:LINKS_PER_PAGE]
   return render_to_response('weblinks/link_summary.html', {
      'links': links, 
      'title': 'Newest Links',
      },
      context_instance = RequestContext(request))

#######################################################################

def popular_links(request):
   links = Link.public_objects.order_by('-hits')[:LINKS_PER_PAGE]
   return render_to_response('weblinks/link_summary.html', {
      'links': links, 
      'title': 'Popular Links',
      },
      context_instance = RequestContext(request))

#######################################################################

@login_required
def add_link(request):
   if request.method == 'POST':
      add_form = AddLinkForm(request.POST)
      if add_form.is_valid():
         new_link = add_form.save(commit=False)
         new_link.user = request.user
         new_link.is_public = False
         new_link.save()
         email_admins('New link for approval', """Hello,

A user has added a new link for your approval.
""")
         return HttpResponseRedirect(reverse('weblinks.views.add_thanks'))
   else:
      add_form = AddLinkForm()

   return render_to_response('weblinks/add_link.html', {
      'add_form': add_form,
      },
      context_instance = RequestContext(request))

#######################################################################

@login_required
def add_thanks(request):
   return render_to_response('weblinks/add_link.html', {
      },
      context_instance = RequestContext(request))

#######################################################################

# Maps URL component to database field name for the links table:

LINK_FIELD_MAP = {
   'title': 'title', 
   'date': '-date_added',
   'hits': '-hits'
}

def view_links(request, category, sort='title', page='1'):
   try:
      cat = Category.objects.get(pk=category)
   except Category.DoesNotExist:
      raise Http404

   if sort in LINK_FIELD_MAP:
      order_by = LINK_FIELD_MAP[sort]
   else:
      sort = 'title'
      order_by = LINK_FIELD_MAP['title']

   links = Link.public_objects.filter(category = category).order_by(order_by)
   paginator = create_paginator(links)
   try:
      the_page = paginator.page(int(page))
   except InvalidPage:
      raise Http404

   return render_to_response('weblinks/view_links.html', {
      's' : sort,
      'category' : cat,
      'page' : the_page, 
      }, 
      context_instance = RequestContext(request))

#######################################################################

def _visit_link(request, link):
   link.hits += 1
   link.save()
   return HttpResponseRedirect(link.url)

#######################################################################

def visit(request, link_id):
   link = get_object_or_404(Link, pk = link_id)
   return _visit_link(request, link)

#######################################################################

def random_link(request):
   ids = Link.public_objects.values_list('id', flat=True)
   if not ids:
       raise Http404
   id = random.choice(ids)
   random_link = Link.public_objects.get(pk=id)
   return _visit_link(request, random_link)

#######################################################################

@require_POST
def report_link(request, link_id):
    """
    This function is the target of an AJAX POST to report a link as dead.
    """
    if not request.user.is_authenticated():
        return HttpResponse('Please login or register to report a broken link.')

    try:
        link = Link.objects.get(pk=link_id)
    except Link.DoesNotExist:
        return HttpResponseBadRequest("That link doesn't exist.")

    FlaggedLink.objects.create(link, request.user)
    return HttpResponse("The link was reported. A moderator will review the " \
            "link shortly. Thanks for helping to improve the content on " \
            "this site.")

#######################################################################

def search_links(request, page=1):
   if request.method == 'POST':
      form = SearchForm(request.POST)
      if form.is_valid():
         query_text = form.query()
         page = 1
      else:
         return HttpResponseRedirect(reverse('weblinks.views.link_index'))
   else:
      if 'query' in request.GET:
         query_text = request.GET['query']
      else:
         return HttpResponseRedirect(reverse('weblinks.views.link_index'))

   links = Link.public_objects.filter(
         Q(title__icontains = query_text) |
         Q(description__icontains = query_text)).order_by('title').select_related()
   paginator = create_paginator(links)
   try:
      the_page = paginator.page(int(page))
   except EmptyPage:
      links = Link.public_objects.none()
   except InvalidPage:
      raise Http404

   return render_to_response('weblinks/search_results.html', {
      'query': query_text,
      'page': the_page, 
      }, 
      context_instance = RequestContext(request))

#######################################################################

def link_detail(request, id):
    link = get_object_or_404(Link, pk=id)
    return render_to_response('weblinks/link_detail.html', {
        'link': link, 
        },
        context_instance = RequestContext(request))
