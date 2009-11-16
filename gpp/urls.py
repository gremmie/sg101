from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from news.feeds import LatestNewsFeed

admin.autodiscover()

feeds = {
   'news': LatestNewsFeed,
}

urlpatterns = patterns('',
   url(r'^$', 'views.home', name='home'),
   (r'^admin/doc/', include('django.contrib.admindocs.urls')),
   (r'^admin/', include(admin.site.urls)),
   (r'^accounts/', include('accounts.urls')),
   (r'^calendar/', include('gcalendar.urls')),
   (r'^comments/', include('comments.urls')),
   (r'^contact/', include('contact.urls')),
   (r'^core/', include('core.urls')),
   (r'^donations/', include('donations.urls')),
   (r'^downloads/', include('downloads.urls')),
   url(r'^feeds/(?P<url>.*)/$', 
      'django.contrib.syndication.views.feed', 
      {'feed_dict': feeds },
      'feeds-news'),
   (r'^forums/', include('forums.urls')),
   (r'^irc/', include('irc.urls')),
   (r'^links/', include('weblinks.urls')),
   (r'^member_map/', include('membermap.urls')),
   (r'^messages/', include('messages.urls')),
   (r'^news/', include('news.urls')),
   (r'^podcast/', include('podcast.urls')),
   (r'^polls/', include('polls.urls')),
   (r'^potd/', include('potd.urls')),
   (r'^profile/', include('bio.urls')),
   (r'^shout/', include('shoutbox.urls')),
   (r'^smiley/', include('smiley.urls')),
)

if settings.DEBUG:
   urlpatterns += patterns('',
      (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
   )
