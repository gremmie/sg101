from django.contrib.auth import views as auth_views

from antispam.decorators import rate_limit

SPAM_PHRASE_KEY = "antispam.spam_phrases"
BUSTED_MESSAGE = ("Your post has tripped our spam filter. Your account has "
        "been suspended pending a review of your post. If this was a mistake "
        "then we apologize; your account will be restored shortly.")

# Install rate limiting on auth login
auth_views.login = rate_limit()(auth_views.login)
