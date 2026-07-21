"""
Views for the weblinks application.

"""
import random
from django.shortcuts import render
from django.core.paginator import InvalidPage
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import Http404
from django.views.decorators.http import require_POST

from core.paginator import DiggPaginator
from core.functions import email_admins
from core.functions import get_page
from weblinks.models import Category
from weblinks.models import Link
from weblinks.models import FlaggedLink
from weblinks.forms import AddLinkForm

#######################################################################

LINKS_PER_PAGE = 10

def create_paginator(links):
   return DiggPaginator(links, LINKS_PER_PAGE, body=5, tail=3, margin=3, padding=2)

#######################################################################

def link_index(request):
   categories = Category.objects.all()
   total_links = Link.public_objects.all().count()
   return render(request, 'weblinks/index.html', {
      'categories': categories,
      'total_links': total_links,
      'top_menu': 'categories',
      'V3_DESIGN': True,
      })

#######################################################################

def new_links(request):
   links = Link.public_objects.order_by('-date_added')
   paginator = create_paginator(links)
   page = get_page(request.GET)
   try:
      the_page = paginator.page(page)
   except InvalidPage:
      raise Http404

   return render(request, 'weblinks/link_summary.html', {
      'page': the_page,
      'title': 'Newest Links',
      'top_menu': 'new',
      'V3_DESIGN': True,
      })

#######################################################################

def popular_links(request):
   links = Link.public_objects.order_by('-hits')
   paginator = create_paginator(links)
   page = get_page(request.GET)
   try:
      the_page = paginator.page(page)
   except InvalidPage:
      raise Http404
   return render(request, 'weblinks/link_summary.html', {
      'page': the_page,
      'title': 'Popular Links',
      'top_menu': 'popular',
      'V3_DESIGN': True,
      })

#######################################################################

@login_required
def add_link(request):
   if request.method == 'POST':
      add_form = AddLinkForm(request.POST)
      if add_form.is_valid():
         new_link = add_form.save(commit=False)
         new_link.user = request.user
         new_link.save()
         email_admins('New link for approval', """Hello,

A user has added a new link for your approval.
""")
         return HttpResponseRedirect(reverse('weblinks-add_thanks'))
   else:
      add_form = AddLinkForm()

   return render(request, 'weblinks/add_link.html', {
      'add_form': add_form,
      'top_menu': 'add',
      'V3_DESIGN': True,
      })

#######################################################################

@login_required
def add_thanks(request):
   return render(request, 'weblinks/add_link.html', {
      'V3_DESIGN': True,
      'top_menu': 'add',
      })

#######################################################################

# Maps URL component to database field name for the links table:

LINK_FIELD_MAP = {
   'title': 'title',
   'date': '-date_added',
   'hits': '-hits'
}

def view_links(request, slug, sort='title'):
   try:
      cat = Category.objects.get(slug=slug)
   except Category.DoesNotExist:
      raise Http404

   if sort in LINK_FIELD_MAP:
      order_by = LINK_FIELD_MAP[sort]
   else:
      sort = 'title'
      order_by = LINK_FIELD_MAP['title']

   links = Link.public_objects.filter(category=cat).order_by(order_by)
   paginator = create_paginator(links)
   page = get_page(request.GET)
   try:
      the_page = paginator.page(page)
   except InvalidPage:
      raise Http404

   return render(request, 'weblinks/view_links.html', {
      's' : sort,
      'category' : cat,
      'page' : the_page,
      'V3_DESIGN': True,
      })

#######################################################################

def _visit_link(request, link):
   link.hits += 1
   link.save()
   return HttpResponseRedirect(link.url)

#######################################################################

@require_POST
def visit(request, link_id):
   link = get_object_or_404(Link, pk = link_id)
   return _visit_link(request, link)

#######################################################################

def random_link(request):
    if request.method == 'POST':
        ids = Link.public_objects.values_list('id', flat=True)
        if not ids:
           raise Http404
        the_id = random.choice(ids)
        random_link = Link.public_objects.get(pk=the_id)
        return _visit_link(request, random_link)

    return render(request, 'weblinks/random_link.html', {
        'top_menu': 'random',
        'V3_DESIGN': True,
        })

#######################################################################

@require_POST
def report_link(request, link_id):
    """
    This function is the target of an AJAX POST to report a link as dead.
    """
    if not request.user.is_authenticated:
        return HttpResponse('Please login or register to report a broken link.')

    try:
        link = Link.objects.get(pk=link_id)
    except Link.DoesNotExist:
        return HttpResponseBadRequest("That link doesn't exist.")

    FlaggedLink.objects.create(link, request.user)
    return HttpResponse("The link was reported. A moderator will review the "
            "link shortly. Thanks for helping to improve the content on "
            "this site.")

#######################################################################

def link_detail(request, id):
    link = get_object_or_404(Link, pk=id)
    if not link.is_public:
        raise Http404
    return render(request, 'weblinks/link_detail.html', {
        'link': link,
        'V3_DESIGN': True,
        })
