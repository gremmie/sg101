"""
Views for the ygroup (Yahoo Group Archive) application.

"""
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView

from ygroup.models import Thread, Post
from core.paginator import DiggPaginator


THREADS_PER_PAGE = 40
POSTS_PER_PAGE = 20


class ThreadIndexView(ListView):
    """
    This generic view displays the list of threads available.

    """
    model = Thread
    paginate_by = THREADS_PER_PAGE
    template_name = 'ygroup/v3/thread_list.html'

    def get_context_data(self, **kwargs):
        context = super(ThreadIndexView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context

    def get_paginator(self, queryset, per_page, **kwargs):
        """
        Return an instance of the paginator for this view.
        """
        return DiggPaginator(queryset, per_page, body=5, tail=2,
                margin=3, padding=2, **kwargs)


class ThreadView(ListView):
    """
    This generic view displays the posts in a thread.

    """
    context_object_name = "post_list"
    template_name = "ygroup/v3/thread.html"
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        self.thread = get_object_or_404(Thread, pk=self.args[0])
        return Post.objects.filter(thread=self.thread)

    def get_context_data(self, **kwargs):
        context = super(ThreadView, self).get_context_data(**kwargs)
        context['thread'] = self.thread
        context['V3_DESIGN'] = True
        return context

    def get_paginator(self, queryset, per_page, **kwargs):
        """
        Return an instance of the paginator for this view.
        """
        return DiggPaginator(queryset, per_page, body=5, tail=2,
                margin=3, padding=2, **kwargs)


class PostView(DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'ygroup/v3/post.html'

    def get_context_data(self, **kwargs):
        context = super(PostView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context
