"""
Views for the News application.
"""

import datetime
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.paginator import InvalidPage
from django.urls import reverse
from django.contrib.sites.models import Site
from django.http import Http404

from tagging.models import Tag
from tagging.models import TaggedItem

from core.functions import send_mail
from core.functions import get_full_name
from core.functions import get_page
from core.paginator import DiggPaginator
from news.models import Category
from news.models import Story
from news.forms import AddNewsForm
from news.forms import SendStoryForm
from news.utils import attach_extra_attrs


NEWS_PER_PAGE = 10

#######################################################################

def create_paginator(stories):
    return DiggPaginator(stories, NEWS_PER_PAGE, body=5, tail=3, margin=3, padding=2)

#######################################################################

def index(request):
    # Defer the tags field because we are going to get all the
    # tags out in 1 query later...
    stories = Story.objects.all().defer('tags').select_related(
            'submitter', 'category', 'forums_topic')
    paginator = create_paginator(stories)

    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    # Go get the tags and comment counts for all these stories in bulk rather
    # than one at a time in the template; this saves database queries
    attach_extra_attrs(the_page.object_list)

    return render(request, 'news/index.html', {
        'title': 'Main Index',
        'page': the_page,
        'section': 'main',
        'V3_DESIGN': True,
        })

#######################################################################

def archive_index(request):
    dates = Story.objects.dates('date_submitted', 'month', order='DESC')
    return render(request, 'news/archive_index.html', {
        'title': 'News Archive',
        'dates': dates,
        'section': 'archives',
        'V3_DESIGN': True,
        })

#######################################################################

def archive(request, year, month):
    stories = Story.objects.defer('tags').filter(date_submitted__year=year,
            date_submitted__month=month).select_related(
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
        cat_list.append((cat, cat.story_set.defer('tags')[:10]))

    return render(request, 'news/category_index.html', {
        'cat_list': cat_list,
        'section': 'categories',
        'V3_DESIGN': True,
        })

#######################################################################

def category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    stories = Story.objects.defer('tags').filter(category=category).select_related(
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
    tags = Tag.objects.cloud_for_model(Story)
    return render(request, 'news/tag_index.html', {
        'tags': tags,
        'section': 'tags',
        'V3_DESIGN': True,
        })

#######################################################################

def tag(request, tag_name):
    # Tags are stored lowercased (FORCE_LOWERCASE_TAGS), so a mixed-case tag in
    # the URL has to be matched without regard to case.
    tag = get_object_or_404(Tag, name__iexact=tag_name)
    stories = TaggedItem.objects.get_by_model(
            Story.objects.defer('tags').select_related(
                'submitter', 'category', 'forums_topic'), tag)
    paginator = create_paginator(stories)
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

#######################################################################

@login_required
def email_story(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    if request.method == 'POST':
        send_form = SendStoryForm(request.POST)
        if send_form.is_valid():
            site = Site.objects.get_current()
            to_name = send_form.name()
            to_email = send_form.email()
            from_name = get_full_name(request.user)
            from_email = settings.GPP_NO_REPLY_EMAIL + '@' + site.domain

            msg = render_to_string('news/send_story_email.txt',
                    {
                        'to_name': to_name,
                        'sender_name': from_name,
                        'site_name' : site.name,
                        'site_url' : site.domain,
                        'story_title': story.title,
                        'story_link': story.get_absolute_url(),
                    })

            subject = 'Interesting Story at ' + site.name
            send_mail(subject, msg, from_email, [to_email], reply_to=request.user.email)
            return HttpResponseRedirect(reverse('news-email_thanks',
                                                args=[story_id]))
    else:
        send_form = SendStoryForm()

    return render(request, 'news/send_story.html', {
        'send_form': send_form,
        'story': story,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def email_thanks(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    return render(request, 'news/send_story.html', {
        'story': story,
        'V3_DESIGN': True,
        })
