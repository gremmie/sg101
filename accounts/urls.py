"""urls for the accounts application"""
from django.conf.urls import patterns, url
from django.conf import settings
from django.views.generic import TemplateView

urlpatterns = patterns('accounts.views',
    url(r'^register/$', 'register', name='accounts-register'),
    (r'^register/thanks/$', 'register_thanks'),
    (r'^register/confirm/(?P<username>[\w.@+-]{1,30})/(?P<key>[a-zA-Z0-9]{20})/$', 'register_confirm'),
)

urlpatterns += patterns('',
    url(r'^login/$',
        'django.contrib.auth.views.login',
        kwargs={'template_name': 'accounts/login.html'},
        name='accounts-login'),
    url(r'^logout/$',
        'django.contrib.auth.views.logout',
        kwargs={'template_name': 'accounts/logout.html'},
        name='accounts-logout'),
    (r'^password/$',
        'django.contrib.auth.views.password_change',
        {'template_name': 'accounts/password_change.html',
         'post_change_redirect': settings.LOGIN_REDIRECT_URL}),
    url(r'^password/reset/$',
        'django.contrib.auth.views.password_reset',
        kwargs={'template_name': 'accounts/password_reset.html',
         'email_template_name': 'accounts/password_reset_email.txt',
         'post_reset_redirect': '/accounts/password/reset/sent/'},
        name='accounts-password_reset'),
    url(r'^password/reset/sent/$',
        'django.contrib.auth.views.password_reset_done',
        kwargs={'template_name': 'accounts/password_reset_sent.html'},
        name='accounts-password_reset_sent'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9a-z]+)/(?P<token>[0-9a-z]+-\w+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        kwargs={
            'template_name': 'accounts/password_reset_confirm.html',
            'post_reset_redirect': '/accounts/password/reset/success/',
            },
        name='accounts-password_reset_confirm'),
    url(r'^password/reset/success/$',
        'django.contrib.auth.views.password_reset_complete',
        kwargs={'template_name': 'accounts/password_reset_complete.html'},
        name='accounts-password_reset_success'),
    url(r'^username/query/$',
        'accounts.views.username_query',
        name='accounts-username_query'),
    url(r'^username/sent/$',
        TemplateView.as_view(template_name='accounts/username_sent.html'),
        name='accounts-username_sent'),
)

