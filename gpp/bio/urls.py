"""urls for the bio application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('bio.views',
    url(r'^members/(?P<type>user|date)/page/(?P<page>\d+)/$', 
        'member_list', 
        name='bio-members_full'),
    url(r'^me/$', 'my_profile', name='bio-me'),
    url(r'^view/(?P<username>\w{1,30})/$', 'view_profile', name='bio-view_profile'),
    url(r'^edit/$', 'edit_profile', name='bio-edit_profile'),
    url(r'^edit/elsewhere/$', 'edit_elsewhere', name='bio-edit_elsewhere'),
    url(r'^avatar/$', 'change_avatar', name='bio-change_avatar'),
    url(r'^flag/(\d+)/$', 'flag_profile', name='bio-flag_profile'),
)

urlpatterns += patterns('django.views.generic.simple',
    url(r'^members/$', 
        'redirect_to', 
        {'url': '/profile/members/user/page/1/'},
        name='bio-members'),
)

