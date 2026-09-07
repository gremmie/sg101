"""
Views for the News application.
"""

import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone
from django.http import HttpResponsePermanentRedirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.paginator import InvalidPage
from django.urls import reverse
from django.http import Http404

from core.functions import get_page
from core.paginator import DiggPaginator
from news.models import Category
from news.models import Story
from news.forms import AddNewsForm
from news.tag_cloud import tag_cloud
from news.utils import attach_extra_attrs


NEWS_PER_PAGE = 10

#######################################################################

def create_paginator(stories):
    return DiggPaginator(stories, NEWS_PER_PAGE, body=5, tail=3, margin=3, padding=2)

#######################################################################

def index(request):
    stories = Story.objects.all().select_related(
            'submitter', 'category', 'forums_topic')
    paginator = create_paginator(stories)

    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    # Go get the comment counts for all these stories in bulk rather than one
    # at a time in the template; this saves database queries
    attach_extra_attrs(the_page.object_list)

    return render(request, 'news/index.html', {
        'title': 'Main Index',
        'page': the_page,
        'section': 'main',
        'V3_DESIGN': True,
        })

#######################################################################

def archive_index(request):
    # dates() reads the active timezone, and it reads it when the queryset is
    # evaluated -- which would be inside the template, long after any override
    # here had exited. Hence the list(): the months are resolved in TIME_ZONE
    # now, while the zone is still named. See in_month() in donations/models.py
    # for the same problem solved the other way.
    with timezone.override(settings.TIME_ZONE):
        dates = list(Story.objects.dates('date_submitted', 'month',
                                         order='DESC'))
    return render(request, 'news/archive_index.html', {
        'title': 'News Archive',
        'dates': dates,
        'section': 'archives',
        'V3_DESIGN': True,
        })

#######################################################################

def archive(request, year, month):
    # tzinfo, not the active zone: this queryset is paginated, so it is
    # evaluated well after this function returns.
    site_tz = ZoneInfo(settings.TIME_ZONE)
    stories = Story.objects.annotate(
            _year=ExtractYear('date_submitted', tzinfo=site_tz),
            _month=ExtractMonth('date_submitted', tzinfo=site_tz),
        ).filter(_year=year, _month=month).select_related(
                'submitter', 'category', 'forums_topic')
    paginator = create_paginator(stories)
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    attach_extra_attrs(the_page.object_list)

    month_name = datetime.date(int(year), int(month), 1).strftime('%B')

    return render(request, 'news/index.html', {
        'title': 'Archive for %s, %s' % (month_name, year),
        'page': the_page,
        'section': 'archives',
        'V3_DESIGN': True,
        })

#######################################################################

def category_index(request):
    categories = Category.objects.all().select_related()
    cat_list = []
    for cat in categories:
        cat_list.append((cat, cat.story_set.all()[:10]))

    return render(request, 'news/category_index.html', {
        'cat_list': cat_list,
        'section': 'categories',
        'V3_DESIGN': True,
        })

#######################################################################

def category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    stories = Story.objects.filter(category=category).select_related(
                    'submitter', 'category', 'forums_topic')
    paginator = create_paginator(stories)
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    attach_extra_attrs(the_page.object_list)

    return render(request, 'news/index.html', {
        'title': 'Category: ' + category.title,
        'page': the_page,
        'section': 'categories',
        'V3_DESIGN': True,
        })

#######################################################################

def story(request, story_id):
    story = get_object_or_404(Story.objects.select_related(
                'submitter', 'category', 'forums_topic'), pk=story_id)
    return render(request, 'news/story.html', {
        'story': story,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def submit(request):
    if request.method == "POST":
        add_form = AddNewsForm(request.POST)
        if add_form.is_valid():
            add_form.save(request.user)
            return HttpResponseRedirect(reverse('news-submit_thanks'))
    else:
        add_form = AddNewsForm()

    return render(request, 'news/submit_news.html', {
        'add_form': add_form,
        'section': 'submit',
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def submit_thanks(request):
    return render(request, 'news/submit_news.html', {
        'V3_DESIGN': True,
        })

#######################################################################

def tags(request):
    tags = tag_cloud(Story)
    return render(request, 'news/tag_index.html', {
        'tags': tags,
        'section': 'tags',
        'V3_DESIGN': True,
        })

#######################################################################

def tag(request, tag_name):
    # Tags are stored lowercased, so every case variant of a tag names the same
    # page. Send those to the canonical URL rather than serving one page at
    # several addresses under a heading echoing whatever the visitor typed.
    if tag_name != tag_name.lower():
        url = reverse('news-tag_page', kwargs={'tag_name': tag_name.lower()})
        query = request.META.get('QUERY_STRING')
        return HttpResponsePermanentRedirect(
                '%s?%s' % (url, query) if query else url)

    stories = Story.objects.filter(
            tags__contains=[tag_name]).select_related(
                'submitter', 'category', 'forums_topic')
    paginator = create_paginator(stories)
    # There is no tag table left to 404 on a missing row, so a tag nothing
    # carries has to be caught here or it would render an empty page. The count
    # is a query the paginator runs regardless.
    if paginator.count == 0:
        raise Http404
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    attach_extra_attrs(the_page.object_list)

    return render(request, 'news/index.html', {
        'title': 'Stories with tag: "%s"' % tag_name,
        'page': the_page,
        'V3_DESIGN': True,
        })
