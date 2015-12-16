"""urls for the bio application"""
from django.conf.urls import url

import bio.views

urlpatterns = [
    url(r'^members/(?P<type>user|date)/$',
        bio.views.member_list,
        name='bio-member_list'),
    url(r'^members/search/$', bio.views.member_search, name='bio-member_search'),
    url(r'^me/$', bio.views.my_profile, name='bio-me'),
    url(r'^view/(?P<username>[\w.@+-]{1,30})/$', bio.views.view_profile, name='bio-view_profile'),
    url(r'^edit/$', bio.views.edit_profile, name='bio-edit_profile'),
    url(r'^edit/elsewhere/$', bio.views.edit_elsewhere, name='bio-edit_elsewhere'),
    url(r'^avatar/$', bio.views.change_avatar, name='bio-change_avatar'),
    url(r'^flag/(\d+)/$', bio.views.flag_profile, name='bio-flag_profile'),
]
