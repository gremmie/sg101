from django.contrib.auth import views as auth_views

from antispam.decorators import log_auth_failures
import antispam.receivers

SPAM_PHRASE_KEY = "antispam.spam_phrases"
BUSTED_MESSAGE = ("Your post has tripped our spam filter. Your account has "
        "been suspended pending a review of your post. If this was a mistake "
        "then we apologize; your account will be restored shortly.")

# Install rate limiting on auth login
auth_views.login = log_auth_failures('Login')(auth_views.login)
