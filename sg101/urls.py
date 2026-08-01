from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from news.feeds import LatestNewsFeed
from forums.feeds import ForumsFeed
from core.views import FixedView
from sg101.views import HomePageView
from sg101.views import StoreView


urlpatterns = [
   path('',
       HomePageView.as_view(),
       name='home'),
   path('about/',
       FixedView.as_view(title='About', content_template='fixed/about.html'),
       name='about'),
   path('colophon/',
       FixedView.as_view(title='Colophon', content_template='fixed/colophon.html'),
       name='colophon'),
   path('policy/privacy/',
       FixedView.as_view(title='Privacy Policy', content_template='fixed/privacy.html'),
       name='privacy'),
   path('policy/tos/',
       FixedView.as_view(title='Terms of Service', content_template='fixed/tos.html'),
       name='tos'),

   path('admin/doc/', include('django.contrib.admindocs.urls')),

   # The admin login page offers a "Forgotten your password?" link when this
   # name resolves. Send it to the site's own reset flow rather than running a
   # second one: these routes used to point at a parallel set of auth views
   # whose companion routes were never named, so the flow raised NoReverseMatch
   # on submit, and its confirm URL still expected the pre-1.6 uidb36 format.
   path('admin/password_reset/',
       RedirectView.as_view(pattern_name='accounts-password_reset',
                            permanent=False),
       name='admin_password_reset'),

   path('store/',
       StoreView.as_view(),
       name='store'),

   path('admin/', admin.site.urls),
   path('accounts/', include('accounts.urls')),
   path('antispam/', include('antispam.urls')),
   path('bandmap/', include('bandmap.urls')),
   path('calendar/', include('gcalendar.urls')),
   path('comments/', include('comments.urls')),
   path('contact/', include('contact.urls')),
   path('contests/', include('contests.urls')),
   path('core/', include('core.urls')),
   path('donations/', include('donations.urls')),
   path('downloads/', include('downloads.urls')),
   path('feeds/news/',
       cache_page(6 * 60 * 60)(LatestNewsFeed()),
       name='feeds-news'),
   path('feeds/forums/',
       cache_page(5 * 60)(ForumsFeed()),
       {'forum_slug': None},
       'feeds-forum_combined'),
   path('feeds/forums/<slug:forum_slug>/',
       cache_page(5 * 60)(ForumsFeed()),
       name='feeds-forum'),
   path('forums/', include('forums.urls')),
   path('links/', include('weblinks.urls')),
   path('messages/', include('messages.urls')),
   path('news/', include('news.urls')),
   path('oembed/', include('oembed.urls')),
   path('podcast/', include('podcast.urls')),
   path('polls/', include('polls.urls')),
   path('potd/', include('potd.urls')),
   path('profile/', include('bio.urls')),
   path('search/', include('search.urls')),
   path('shout/', include('shoutbox.urls')),
   path('smiley/', include('smiley.urls')),
   path('user_photos/', include('user_photos.urls')),
   path('ygroup/', include('ygroup.urls')),
]

# For serving media files in development only:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Django Debug Toolbar (dev only): its URLs must be registered explicitly so the
# toolbar can reverse its own 'djdt' namespace. Guarded to match the app +
# middleware activation in settings/local.py.
if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
