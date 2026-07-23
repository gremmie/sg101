"""urls for the polls application"""
from django.urls import path

import polls.views


urlpatterns = [
    path('', polls.views.poll_index, name='polls-main'),
    path('<int:poll_id>/', polls.views.poll_detail, name='polls-detail'),
    path('<int:poll_id>/vote/', polls.views.poll_vote, name='polls-vote'),
    path('delete_vote/', polls.views.poll_delete_vote, name='polls-delete_vote'),
]
