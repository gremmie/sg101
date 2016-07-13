"""urls for the accounts application"""
from django.conf.urls import url
from django.conf import settings
import django.contrib.auth.views as auth_views
from django.views.generic import TemplateView

import accounts.views

urlpatterns = [
    url(r'^register/$', accounts.views.register, name='accounts-register'),
    url(r'^register/1/$', accounts.views.register1, name='accounts-register1'),
    url(r'^register/2/$', accounts.views.register2, name='accounts-register2'),
    url(r'^register/code/$', accounts.views.get_code, name='accounts-code'),
    url(r'^register/thanks/$', accounts.views.register_thanks, name='accounts-register_thanks'),
    url(r'^register/confirm/(?P<username>[\w.@+-]{1,30})/(?P<key>[a-zA-Z0-9]{20})/$',
        accounts.views.register_confirm,
        name='accounts-register_confirm'),
]

urlpatterns += [
    url(r'^login/$',
        auth_views.login,
        kwargs={
            'template_name': 'accounts/login.html',
            'extra_context': {'V3_DESIGN': True},
        },
        name='accounts-login'),
    url(r'^logout/$',
        auth_views.logout,
        kwargs={
            'template_name': 'accounts/logout.html',
            'extra_context': {'V3_DESIGN': True},
        },
        name='accounts-logout'),
    url(r'^password/$',
        auth_views.password_change,
        {'template_name': 'accounts/password_change.html',
         'post_change_redirect': settings.LOGIN_REDIRECT_URL},
        name='accounts-password_change'),
    url(r'^password/reset/$',
        auth_views.password_reset,
        kwargs={'template_name': 'accounts/password_reset.html',
         'email_template_name': 'accounts/password_reset_email.txt',
         'post_reset_redirect': '/accounts/password/reset/sent/'},
        name='accounts-password_reset'),
    url(r'^password/reset/sent/$',
        auth_views.password_reset_done,
        kwargs={'template_name': 'accounts/password_reset_sent.html'},
        name='accounts-password_reset_sent'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9a-z]+-\w+)/$',
        auth_views.password_reset_confirm,
        kwargs={
            'template_name': 'accounts/password_reset_confirm.html',
            'post_reset_redirect': '/accounts/password/reset/success/',
            },
        name='accounts-password_reset_confirm'),
    url(r'^password/reset/success/$',
        auth_views.password_reset_complete,
        kwargs={'template_name': 'accounts/password_reset_complete.html'},
        name='accounts-password_reset_success'),
    url(r'^username/query/$',
        accounts.views.username_query,
        name='accounts-username_query'),
    url(r'^username/sent/$',
        accounts.views.UsernameSentView.as_view(),
        name='accounts-username_sent'),
]
