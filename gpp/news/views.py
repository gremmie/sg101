"""
Views for the News application.
"""

import datetime
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.paginator import InvalidPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.contrib.sites.models import Site
from django.http import Http404

from tagging.models import Tag
from tagging.models import TaggedItem

from core.html import clean_html
from core.functions import send_mail
from core.functions import get_full_name
from core.paginator import DiggPaginator
from news.models import Category
from news.models import PendingStory
from news.models import Story
from news.forms import AddNewsForm
from news.forms import SearchNewsForm
from news.forms import SendStoryForm

NEWS_PER_PAGE = 2

#######################################################################

def create_paginator(stories):
   return DiggPaginator(stories, NEWS_PER_PAGE, body=5, tail=3, margin=3, padding=2)

#######################################################################

def index(request, page=1):
   stories = Story.objects.all().select_related()
   paginator = create_paginator(stories)
   try:
      the_page = paginator.page(int(page))
   except InvalidPage:
      raise Http404

   return render_to_response('news/index.html', {
      'title': 'Main Index',
      'page': the_page,
      'search_form': SearchNewsForm(),
      }, 
      context_instance = RequestContext(request))

#######################################################################

def archive_index(request):
   dates = Story.objects.dates('date_submitted', 'month', order='DESC')
   return render_to_response('news/archive_index.html', {
      'title': 'News Archive',
      'dates': dates, 
      'search_form': SearchNewsForm(),
      }, 
      context_instance = RequestContext(request))

#######################################################################

def archive(request, year, month, page=1):
   stories = Story.objects.filter(date_submitted__year=year, date_submitted__month=month)
   paginator = create_paginator(stories)
   try:
      the_page = paginator.page(int(page))
   except InvalidPage:
      raise Http404

   month_name = datetime.date(int(year), int(month), 1).strftime('%B')

   return render_to_response('news/index.html', {
      'title': 'Archive for %s, %s' % (month_name, year),
      'page': the_page,
      'search_form': SearchNewsForm(),
      }, 
      context_instance = RequestContext(request))

#######################################################################

def category_index(request):
   categories = Category.objects.all().select_related()
   cat_list = []
   for cat in categories:
      cat_list.append((cat, cat.story_set.defer('tags')[:10]))

   return render_to_response('news/category_index.html', {
      'cat_list': cat_list, 
      'search_form': SearchNewsForm(),
      }, 
      context_instance = RequestContext(request))

#######################################################################

def category(request, category, page=1):
   category = get_object_or_404(Category, pk=category)
   stories = Story.objects.filter(category=category)
   paginator = create_paginator(stories)
   try:
      the_page = paginator.page(int(page))
   except InvalidPage:
      raise Http404

   return render_to_response('news/index.html', {
      'title': 'Category: ' + category.title,
      'page': the_page,
      'search_form': SearchNewsForm(),
      }, 
      context_instance = RequestContext(request))

#######################################################################

def search(request, page=1):
   if request.method == 'POST':
      form = SearchNewsForm(request.POST)
      if form.is_valid():
         query_text = form.get_query()
         category = form.get_category()
         page = 1
      else:
         return HttpResponseRedirect(reverse('news.views.index'))
   else:
      if 'query' in request.GET:
         query_text = request.GET['query']
         category = request.GET.get('category', None)
      else:
         return HttpResponseRedirect(reverse('news.views.index'))

   if category is not None:
      stories = Story.objects.filter(category=category)
      cat_qual = ' in category "%s"' % category.title
   else:
      stories = Story.objects.all()
      cat_qual = ''

   stories = stories.filter(
         Q(title__icontains=query_text) |
         Q(short_text__icontains=query_text) |
         Q(long_text__icontains=query_text)).order_by('-date_submitted')

   paginator = create_paginator(stories)
   try:
      the_page = paginator.page(int(page))
   except InvalidPage:
      raise Http404

   return render_to_response('news/index.html', {
      'title': 'Search Results for "%s"%s' % (query_text, cat_qual),
      'query': query_text,
      'page': the_page,
      'search_form': SearchNewsForm(),
      }, 
      context_instance = RequestContext(request))

#######################################################################

def story(request, story_id):
   story = get_object_or_404(Story, pk=story_id)
   return render_to_response('news/story.html', {
      'story': story,
      'search_form': SearchNewsForm(),
      },
      context_instance=RequestContext(request))

#######################################################################

@login_required
def submit(request):
   if request.method == "POST":
      add_form = AddNewsForm(request.POST)
      if add_form.is_valid():
         pending_story = add_form.save(commit=False)
         pending_story.submitter = request.user
         pending_story.short_text = clean_html(pending_story.short_text)
         pending_story.long_text = clean_html(pending_story.long_text)
         pending_story.save()
         return HttpResponseRedirect(reverse('news.views.submit_thanks'))
   else:
      add_form = AddNewsForm()

   return render_to_response('news/submit_news.html', {
      'add_form': add_form,
      'search_form': SearchNewsForm(),
      },
      context_instance = RequestContext(request))

#######################################################################

@login_required
def submit_thanks(request):
   return render_to_response('news/submit_news.html', {
      'search_form': SearchNewsForm(),
      },
      context_instance = RequestContext(request))

#######################################################################

def tags(request):
   tags = Tag.objects.cloud_for_model(Story)
   return render_to_response('news/tag_index.html', {
      'tags': tags,
      'search_form': SearchNewsForm(),
      },
      context_instance = RequestContext(request))

#######################################################################

def tag(request, tag_name, page=1):
   tag = get_object_or_404(Tag, name=tag_name)
   stories = TaggedItem.objects.get_by_model(Story.objects.all().select_related(), tag)
   paginator = create_paginator(stories)
   try:
      the_page = paginator.page(int(page))
   except InvalidPage:
      raise Http404

   return render_to_response('news/index.html', {
      'title': 'Stories with tag: "%s"' % tag_name,
      'page': the_page,
      'search_form': SearchNewsForm(),
      }, 
      context_instance=RequestContext(request))

#######################################################################

@login_required
def email_story(request, story_id):
   story = get_object_or_404(Story, pk=story_id)
   if request.method == 'POST':
      send_form = SendStoryForm(request.POST)
      if send_form.is_valid():
         to_name = send_form.name()
         to_email = send_form.email()
         from_name = get_full_name(request.user)
         from_email = request.user.email
         site = Site.objects.get_current()

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
         send_mail(subject, msg, from_email, [to_email])
         return HttpResponseRedirect(reverse('news.views.email_thanks'))
   else:
      send_form = SendStoryForm()

   return render_to_response('news/send_story.html', {
      'send_form': send_form,
      'story': story,
      },
      context_instance = RequestContext(request))

#######################################################################

@login_required
def email_thanks(request):
   return render_to_response('news/send_story.html', {
      },
      context_instance = RequestContext(request))

