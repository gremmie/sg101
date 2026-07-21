"""urls for the accounts application"""
from django.conf.urls import url
from django.conf import settings
from django.urls import reverse_lazy
import django.contrib.auth.views as auth_views

from antispam.decorators import log_auth_failures
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
    # log_auth_failures records failed POSTs to the auth log that fail2ban
    # watches. It used to be installed by monkeypatching the login view in
    # antispam's AppConfig.ready(); wrapping the view here is equivalent and
    # survives the move to class-based auth views.
    url(r'^login/$',
        log_auth_failures('Login')(auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            extra_context={'V3_DESIGN': True},
        )),
        name='accounts-login'),
    url(r'^logout/$',
        auth_views.LogoutView.as_view(
            template_name='accounts/logout.html',
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-logout'),
    url(r'^password/$',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            # LOGIN_REDIRECT_URL is a URL name; success_url is used verbatim,
            # so it has to be reversed here (the old view did that itself).
            success_url=reverse_lazy(settings.LOGIN_REDIRECT_URL),
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_change'),
    url(r'^password/reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.txt',
            success_url=reverse_lazy('accounts-password_reset_sent'),
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_reset'),
    url(r'^password/reset/sent/$',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_sent.html',
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_reset_sent'),
    # PasswordResetConfirmView answers a valid token with a redirect to this
    # same route with the token replaced by the literal 'set-password' (the
    # real one moves into the session), then serves the form there. That
    # placeholder matches the token pattern below, so it needs no change.
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts-password_reset_success'),
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_reset_confirm'),
    url(r'^password/reset/success/$',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_reset_success'),
    url(r'^username/query/$',
        accounts.views.username_query,
        name='accounts-username_query'),
    url(r'^username/sent/$',
        accounts.views.UsernameSentView.as_view(),
        name='accounts-username_sent'),
]
