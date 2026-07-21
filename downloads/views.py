"""
Views for the downloads application.
"""
import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.core.paginator import InvalidPage
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.paginator import DiggPaginator
from core.functions import email_admins
from core.functions import get_page
from downloads.models import Category
from downloads.models import Download
from downloads.models import VoteRecord
from downloads.forms import AddDownloadForm

#######################################################################

DLS_PER_PAGE = 10

def create_paginator(dls):
   return DiggPaginator(dls, DLS_PER_PAGE, body=5, tail=3, margin=3, padding=2)

#######################################################################

@login_required
def index(request):
    categories = Category.objects.all()
    total_dls = Download.public_objects.all().count()
    return render(request, 'downloads/index.html', {
        'categories': categories,
        'total_dls': total_dls,
        'top_menu': 'categories',
        'V3_DESIGN': True,
        })

#######################################################################
# Maps URL component to database field name for the Download table:

DOWNLOAD_FIELD_MAP = {
   'title': 'title',
   'date': '-date_added',
   'rating': '-average_score',
   'hits': '-hits'
}

@login_required
def category(request, slug, sort='title'):

    cat = get_object_or_404(Category, slug=slug)

    if sort not in DOWNLOAD_FIELD_MAP:
        sort = 'title'
    order_by = DOWNLOAD_FIELD_MAP[sort]

    downloads = Download.public_objects.filter(category=cat.pk).order_by(
            order_by)
    paginator = create_paginator(downloads)
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    return render(request, 'downloads/download_list.html', {
        's' : sort,
        'category' : cat,
        'page' : the_page,
        'top_menu': 'categories',
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def new(request):
    """Display new downloads with pagination."""

    downloads = Download.public_objects.order_by('-date_added')

    paginator = create_paginator(downloads)
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    return render(request, 'downloads/download_summary.html', {
        'page': the_page,
        'title': 'Newest Downloads',
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def popular(request):
    """Display popular downloads with pagination."""

    downloads = Download.public_objects.order_by('-hits')

    paginator = create_paginator(downloads)
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    return render(request, 'downloads/download_summary.html', {
        'page': the_page,
        'title': 'Popular Downloads',
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def rating(request):
    """Display downloads by rating with pagination."""

    downloads = Download.public_objects.order_by('-average_score')
    paginator = create_paginator(downloads)
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    return render(request, 'downloads/download_summary.html', {
        'page': the_page,
        'title': 'Highest Rated Downloads',
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def details(request, id):
    download = get_object_or_404(Download.public_objects, pk=id)
    if not download.is_public:
        raise Http404
    return render(request, 'downloads/download_detail.html', {
        'download' : download,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def add(request):
    if request.method == 'POST':
        form = AddDownloadForm(request.POST, request.FILES)
        if form.is_valid():
            dl = form.save(commit=False)
            dl.user = request.user
            dl.ip_address = request.META.get('REMOTE_ADDR', None)
            dl.save(html=form.html)
            email_admins('New download for approval', """Hello,

A user has uploaded a new download for your approval.
""")
            return HttpResponseRedirect(reverse('downloads-add_thanks'))
    else:
        form = AddDownloadForm()

    return render(request, 'downloads/add.html', {
        'add_form': form,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def thanks(request):
    return render(request, 'downloads/thanks.html', {
        'V3_DESIGN': True,
        })

#######################################################################

@require_POST
def rate_download(request):
    """This function is called by AJAX to rate a download."""
    if request.user.is_authenticated:
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

        download = get_object_or_404(Download.public_objects, pk=id)

        # prevent multiple votes from the same user
        vote_record, created = VoteRecord.objects.get_or_create(
                download=download, user=request.user)
        if created:
            new_score = download.vote(rating)
            download.save()
            return HttpResponse(str(new_score))
        else:
            return HttpResponse('-1')

    return HttpResponseForbidden('You must be logged in to rate a download.')

#######################################################################

@require_POST
def request_download(request):
    """
    This function is called by AJAX to request a download. We update the hit
    count and then return a JSON object of the form:
        { id: download-id, 'url': link-to-download }

    """
    if request.user.is_authenticated:
        dl_id = request.POST.get('id')
        if dl_id:
            try:
                dl = Download.public_objects.get(pk=dl_id)
            except Download.DoesNotExist:
                return HttpResponseNotFound("Download not found")

            dl.hits += 1
            dl.save()

            s = json.dumps({'id': dl_id, 'url': dl.file.url})
            return HttpResponse(s, content_type='application/json')

    return HttpResponseForbidden('An error occurred.')
