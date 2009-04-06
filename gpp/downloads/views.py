"""
Views for the downloads application.
"""
import random

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.views.decorators.http import require_POST

from core.paginator import DiggPaginator
from core.functions import email_admins
from downloads.models import Category
from downloads.models import Download
from downloads.models import VoteRecord
from downloads.forms import AddDownloadForm
from downloads.forms import SearchForm

#######################################################################

DLS_PER_PAGE = 10

def create_paginator(dls):
   return DiggPaginator(dls, DLS_PER_PAGE, body=5, tail=3, margin=3, padding=2)

#######################################################################

@login_required
def index(request):
    categories = Category.objects.all()
    total_dls = Download.public_objects.all().count()
    return render_to_response('downloads/index.html', {
        'categories': categories,
        'total_dls': total_dls,
        },
        context_instance = RequestContext(request))

#######################################################################
# Maps URL component to database field name for the Download table:

DOWNLOAD_FIELD_MAP = {
   'title': 'title', 
   'date': '-date_added',
   'rating': '-average_score',
   'hits': '-hits'
}

@login_required
def category(request, category, sort='title', page='1'):
    try:
        cat = Category.objects.get(pk=category)
    except Category.DoesNotExist:
        raise Http404

    if sort not in DOWNLOAD_FIELD_MAP:
        sort = 'title'
    order_by = DOWNLOAD_FIELD_MAP[sort]

    downloads = Download.public_objects.filter(category=cat.pk).order_by(order_by)
    paginator = create_paginator(downloads)
    try:
        the_page = paginator.page(int(page))
    except InvalidPage:
        raise Http404

    return render_to_response('downloads/download_list.html', {
        's' : sort,
        'category' : cat,
        'page' : the_page, 
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def new(request):
    downloads = Download.public_objects.order_by('-date_added')[:DLS_PER_PAGE]
    return render_to_response('downloads/download_summary.html', {
        'downloads' : downloads,
        'title' : 'Newest Downloads',
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def popular(request):
    downloads = Download.public_objects.order_by('-hits')[:DLS_PER_PAGE]
    return render_to_response('downloads/download_summary.html', {
        'downloads' : downloads,
        'title' : 'Popular Downloads',
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def rating(request):
    downloads = Download.public_objects.order_by('-average_score')[:DLS_PER_PAGE]
    return render_to_response('downloads/download_summary.html', {
        'downloads' : downloads,
        'title' : 'Highest Rated Downloads',
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def download(request, id):
    download = Download.public_objects.get(pk=id)
    if download is None:
        raise Http404
    return _redirect_download(download)

#######################################################################

def _redirect_download(download):
    download.hits += 1
    download.save()
    return HttpResponseRedirect(download.file.url)

#######################################################################

@login_required
def comments(request, id):
    download = Download.public_objects.get(pk=id)
    if download is None:
        raise Http404
    return render_to_response('downloads/download_comments.html', {
        'download' : download,
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def random_download(request):
    ids = Download.public_objects.values_list('id', flat=True)
    if not ids:
        raise Http404
    id = random.choice(ids)
    download = Download.objects.get(pk=id)
    return _redirect_download(download)

#######################################################################

@login_required
def add(request):
    if request.method == 'POST':
        form = AddDownloadForm(request.POST, request.FILES)
        if form.is_valid():
            dl = form.save(commit=False)
            dl.user = request.user
            dl.ip_address = request.META.get('REMOTE_ADDR', None)
            dl.is_public = False
            dl.save()
            email_admins('New download for approval', """Hello,

A user has uploaded a new download for your approval.
""")
            return HttpResponseRedirect(reverse('downloads-add_thanks'))
    else:
        form = AddDownloadForm()

    return render_to_response('downloads/add.html', {
        'add_form': form,
        },
        context_instance=RequestContext(request))

#######################################################################

@login_required
def thanks(request):
    return render_to_response('downloads/thanks.html', {
        },
        context_instance=RequestContext(request))

#######################################################################

@login_required
def search(request, page=1):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query_text = form.query()
            page = 1
        else:
            return HttpResponseRedirect(reverse('downloads-index'))
    else:
        if 'query' in request.GET:
            query_text = request.GET['query']
        else:
            return HttpResponseRedirect(reverse('downloads-index'))

    dls = Download.objects.filter(
            Q(title__icontains = query_text) |
            Q(description__icontains = query_text)).order_by('title')
    paginator = create_paginator(dls)
    try:
        the_page = paginator.page(int(page))
    except EmptyPage:
        dls = Download.objects.none()
    except InvalidPage:
        raise Http404

    return render_to_response('downloads/search_results.html', {
        'query': query_text,
        'page': the_page, 
        }, 
        context_instance = RequestContext(request))

#######################################################################

@require_POST
def rate_download(request):
    """This function is called by AJAX to rate a download."""
    if request.user.is_authenticated():
        id = request.POST.get('id', None)
        rating = request.POST.get('rating', None)
        if id is None or rating is None:
            return HttpResponseBadRequest('Missing id or rating.')
        
        try:
            rating = int(rating)
        except ValueError:
            return HttpResponseBadRequest('Invalid rating.')

        # rating will be from 0-4
        rating = min(5, max(1, rating))

        try:
            download = Download.public_objects.get(pk=id)
        except Download.DoesNotExist:
            return HttpResponseBadRequest('Invalid download id.')

        # prevent multiple votes from the same user
        vote_record, created = VoteRecord.objects.get_or_create(download=download, user=request.user)
        if created:
            new_score = download.vote(rating)
            download.save()
            return HttpResponse(str(new_score))
        else:
            return HttpResponse('-1')

    return HttpResponseForbidden('You must be logged in to rate a download.')
