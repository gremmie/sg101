from django.conf.urls import patterns, url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from haystack.views import search_view_factory

from news.feeds import LatestNewsFeed
from forums.feeds import ForumsFeed
from custom_search.forms import CustomModelSearchForm
from core.views import FixedView


admin.autodiscover()

urlpatterns = patterns('',
   url(r'^$',
       TemplateView.as_view(template_name='home.html'),
       name='home'),
   url(r'^about/$',
       FixedView.as_view(title='About', content_template='fixed/about.html'),
       name='about'),
   (r'^admin/doc/', include('django.contrib.admindocs.urls')),

   url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='admin_password_reset'),
   (r'^admin/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
   (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
   (r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),

   (r'^admin/', include(admin.site.urls)),
   (r'^accounts/', include('accounts.urls')),
   (r'^antispam/', include('antispam.urls')),
   (r'^calendar/', include('gcalendar.urls')),
   (r'^comments/', include('comments.urls')),
   (r'^contact/', include('contact.urls')),
   (r'^contests/', include('contests.urls')),
   (r'^core/', include('core.urls')),
   (r'^donations/', include('donations.urls')),
   (r'^downloads/', include('downloads.urls')),
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
   (r'^forums/', include('forums.urls')),
   (r'^irc/', include('irc.urls')),
   (r'^links/', include('weblinks.urls')),
   (r'^member_map/', include('membermap.urls')),
   (r'^messages/', include('messages.urls')),
   (r'^news/', include('news.urls')),
   (r'^oembed/', include('oembed.urls')),
   (r'^pb/', include('phantombrigade.urls')),
   (r'^podcast/', include('podcast.urls')),
   (r'^polls/', include('polls.urls')),
   (r'^potd/', include('potd.urls')),
   (r'^profile/', include('bio.urls')),
   (r'^shout/', include('shoutbox.urls')),
   (r'^smiley/', include('smiley.urls')),
   (r'^ygroup/', include('ygroup.urls')),
)

# Haystack search views
urlpatterns += patterns('haystack.views',
    url(r'^search/$',
        search_view_factory(form_class=CustomModelSearchForm, load_all=True),
        name='haystack_search'),
)

# For serving media files in development only:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
