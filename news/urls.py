"""urls for the News application"""
from django.urls import path, re_path

import news.views


urlpatterns = [
    path('date/', news.views.index, name='news-index_page'),
    path('archive/', news.views.archive_index, name='news-archive_index'),
    # Regex kept on purpose: the int converter would also match years longer
    # than four digits and months longer than two; these fixed widths matter.
    re_path(r'^archive/(?P<year>\d{4})/(?P<month>\d\d?)/$',
            news.views.archive,
            name='news-archive_page'),
    path('categories/', news.views.category_index, name='news-category_index'),
    path('category/<slug:slug>/', news.views.category, name='news-category'),
    path('story/<int:story_id>/', news.views.story, name='news-story'),
    path('submit/', news.views.submit, name='news-submit'),
    path('submit/thanks/', news.views.submit_thanks, name='news-submit_thanks'),
    path('tags/', news.views.tags, name='news-tag_index'),
    path('tag/<str:tag_name>/', news.views.tag, name='news-tag_page'),
]
