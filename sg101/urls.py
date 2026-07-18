from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
import django.contrib.auth.views
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from news.feeds import LatestNewsFeed
from forums.feeds import ForumsFeed
from core.views import FixedView
from sg101.views import HomePageView
from sg101.views import StoreView


urlpatterns = [
   url(r'^$',
       HomePageView.as_view(),
       name='home'),
   url(r'^about/$',
       FixedView.as_view(title='About', content_template='fixed/about.html'),
       name='about'),
   url(r'^colophon/$',
       FixedView.as_view(title='Colophon', content_template='fixed/colophon.html'),
       name='colophon'),
   url(r'^policy/privacy/$',
       FixedView.as_view(title='Privacy Policy', content_template='fixed/privacy.html'),
       name='privacy'),
   url(r'^policy/tos/$',
       FixedView.as_view(title='Terms of Service', content_template='fixed/tos.html'),
       name='tos'),

   url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

   url(r'^admin/password_reset/$', django.contrib.auth.views.password_reset, name='admin_password_reset'),
   url(r'^admin/password_reset/done/$', django.contrib.auth.views.password_reset_done),
   url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', django.contrib.auth.views.password_reset_confirm),
   url(r'^reset/done/$', django.contrib.auth.views.password_reset_complete),

   url(r'^store/$',
       StoreView.as_view(),
       name='store'),

   url(r'^admin/', admin.site.urls),
   url(r'^accounts/', include('accounts.urls')),
   url(r'^antispam/', include('antispam.urls')),
   url(r'^bandmap/', include('bandmap.urls')),
   url(r'^calendar/', include('gcalendar.urls')),
   url(r'^comments/', include('comments.urls')),
   url(r'^contact/', include('contact.urls')),
   url(r'^contests/', include('contests.urls')),
   url(r'^core/', include('core.urls')),
   url(r'^donations/', include('donations.urls')),
   url(r'^downloads/', include('downloads.urls')),
   url(r'^feeds/news/$',
       cache_page(6 * 60 * 60)(LatestNewsFeed()),
       name='feeds-news'),
   url(r'^feeds/forums/$',
       cache_page(5 * 60)(ForumsFeed()),
       {'forum_slug': None},
       'feeds-forum_combined'),
   url(r'^feeds/forums/(?P<forum_slug>[\w\d-]+)/$',
       cache_page(5 * 60)(ForumsFeed()),
       name='feeds-forum'),
   url(r'^forums/', include('forums.urls')),
   url(r'^links/', include('weblinks.urls')),
   url(r'^messages/', include('messages.urls')),
   url(r'^news/', include('news.urls')),
   url(r'^oembed/', include('oembed.urls')),
   url(r'^podcast/', include('podcast.urls')),
   url(r'^polls/', include('polls.urls')),
   url(r'^potd/', include('potd.urls')),
   url(r'^profile/', include('bio.urls')),
   url(r'^shout/', include('shoutbox.urls')),
   url(r'^smiley/', include('smiley.urls')),
   url(r'^user_photos/', include('user_photos.urls')),
   url(r'^ygroup/', include('ygroup.urls')),
]

# Search is stubbed out: the Xapian/Haystack stack was removed and native
# PostgreSQL full-text search will replace it later. Until then both search
# URLs render a placeholder so existing links don't 404.
urlpatterns += [
   url(r'^search/$',
       FixedView.as_view(title='About', content_template='fixed/about.html'),
       name='haystack_search'),
   url(r'^search/ajax/$',
       FixedView.as_view(title='About', content_template='fixed/about.html'),
       name='haystack_search_ajax'),
]

# For serving media files in development only:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
