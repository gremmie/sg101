"""urls for the bio application"""
from django.urls import path, re_path

import bio.views

urlpatterns = [
    # Regex kept: 'type' is a fixed choice set, not a stock converter shape.
    re_path(r'^members/(?P<type>user|date)/$',
        bio.views.member_list,
        name='bio-member_list'),
    path('members/search/', bio.views.member_search, name='bio-member_search'),
    path('me/', bio.views.my_profile, name='bio-me'),
    # Regex kept: username is length-bounded and allows '.@+-'.
    re_path(r'^view/(?P<username>[\w.@+-]{1,30})/$', bio.views.view_profile,
        name='bio-view_profile'),
    path('edit/', bio.views.edit_profile, name='bio-edit_profile'),
    path('edit/elsewhere/', bio.views.edit_elsewhere, name='bio-edit_elsewhere'),
    path('avatar/', bio.views.change_avatar, name='bio-change_avatar'),
    path('flag/<int:profile_id>/', bio.views.flag_profile, name='bio-flag_profile'),
]
