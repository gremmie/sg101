"""urls for the accounts application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('accounts.views',
    url(r'^register/$', 'register', name='accounts-register'),
    (r'^register/thanks/$', 'register_thanks'),
    (r'^register/confirm/(?P<username>\w{1,30})/(?P<key>[a-zA-Z0-9]{20})/$', 'register_confirm'),
)

urlpatterns += patterns('',
    url(r'^login/',
        'django.contrib.auth.views.login',
        kwargs={'template_name': 'accounts/login.html'},
        name='accounts-login'),
    url(r'^logout/',
        'django.contrib.auth.views.logout',
        kwargs={'template_name': 'accounts/logout.html'},
        name='accounts-logout'), 
    (r'^password/', 
        'django.contrib.auth.views.password_change', 
        {'template_name': 'accounts/password_change.html',
         'post_change_redirect': '/accounts/profile/'}),
)


# vim: ts=4 sw=4
