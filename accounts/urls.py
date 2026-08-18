"""urls for the accounts application"""
from django.conf import settings
from django.urls import path, re_path, reverse_lazy
import django.contrib.auth.views as auth_views

from antispam.decorators import log_auth_failures
from accounts.forms import SitePasswordResetForm
import accounts.views

urlpatterns = [
    path('register/', accounts.views.register, name='accounts-register'),
    path('register/1/', accounts.views.register1, name='accounts-register1'),
    path('register/2/', accounts.views.register2, name='accounts-register2'),
    path('register/code/', accounts.views.get_code, name='accounts-code'),
    path('register/thanks/', accounts.views.register_thanks, name='accounts-register_thanks'),
    # Regex kept: both segments are length-bounded and the key allows only a
    # fixed 20-char alphanumeric run -- no stock path converter expresses that.
    re_path(r'^register/confirm/(?P<username>[\w.@+-]{1,30})/(?P<key>[a-zA-Z0-9]{20})/$',
        accounts.views.register_confirm,
        name='accounts-register_confirm'),
]

urlpatterns += [
    # log_auth_failures records failed POSTs to the auth log that fail2ban
    # watches. It used to be installed by monkeypatching the login view in
    # antispam's AppConfig.ready(); wrapping the view here is equivalent and
    # survives the move to class-based auth views.
    path('login/',
        log_auth_failures('Login')(auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            extra_context={'V3_DESIGN': True},
        )),
        name='accounts-login'),
    path('logout/',
        auth_views.LogoutView.as_view(
            template_name='accounts/logout.html',
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-logout'),
    path('password/',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            # LOGIN_REDIRECT_URL is a URL name; success_url is used verbatim,
            # so it has to be reversed here (the old view did that itself).
            success_url=reverse_lazy(settings.LOGIN_REDIRECT_URL),
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_change'),
    path('password/reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.txt',
            success_url=reverse_lazy('accounts-password_reset_sent'),
            extra_context={'V3_DESIGN': True},
            # Without this the stock form sends the reset email itself,
            # inline in the request and outside the site's mail wrapper.
            form_class=SitePasswordResetForm,
        ),
        name='accounts-password_reset'),
    path('password/reset/sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_sent.html',
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_reset_sent'),
    # PasswordResetConfirmView answers a valid token with a redirect to this
    # same route with the token replaced by the literal 'set-password' (the
    # real one moves into the session), then serves the form there. That
    # placeholder matches the token pattern below, so it needs no change.
    # Regex kept: the token has a specific two-part length-bounded shape. The
    # hash half is 32 chars -- half of a sha256 hexdigest, Django's default token
    # algorithm since 3.1 (it was 20 under the old sha1 default).
    re_path(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts-password_reset_success'),
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_reset_confirm'),
    path('password/reset/success/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
            extra_context={'V3_DESIGN': True},
        ),
        name='accounts-password_reset_success'),
    path('username/query/',
        accounts.views.username_query,
        name='accounts-username_query'),
    path('username/sent/',
        accounts.views.UsernameSentView.as_view(),
        name='accounts-username_sent'),
]
