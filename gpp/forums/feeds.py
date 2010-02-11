"""This file contains the feed class for the forums application."""
import datetime

from django.contrib.syndication.feeds import Feed
from django.core.exceptions import ObjectDoesNotExist

from forums.models import Forum
from forums.models import Post

BASE_YEAR = 2010

class ForumsFeed(Feed):
    """The Feed class for the forums application"""

    def get_object(self, bits):
        # only return public forums
        if len(bits) == 1:
            forum = Forum.objects.get(slug=bits[0])
            if forum.category.groups.count() > 0:
                raise ObjectDoesNotExist
            return forum

        elif len(bits) == 0:
            # return None to indicate we want a combined feed
            return None

    def title(self, obj):
        if obj is None:
            forum_name = 'Combined'
        else:
            forum_name = obj.name

        return 'SurfGuitar101.com %s Forum Feed' % forum_name

    def link(self, obj):
        if obj is None:
            bits = ''
        else:
            bits = obj.slug + '/'

        return '/feeds/forums/' + bits

    def description(self, obj):
        if obj is None:
            return "User posts to SurfGuitar101.com forums."
        return obj.description

    def copyright(self):
        curr_year = datetime.datetime.now().year
        if curr_year == BASE_YEAR:
            year_range = str(BASE_YEAR)
        else:
            year_range = "%d - %d" % (BASE_YEAR, curr_year)

        return 'Copyright (C) %s, SurfGuitar101.com' % year_range

    ttl = '720'

    title_template = 'forums/feed_title.html'
    description_template = 'forums/feed_description.html'
    
    def items(self, obj):
        if obj is None:
            # return a combined feed of public forum threads
            items = Post.objects.filter(
                    topic__forum__in=Forum.objects.public_forums())
        else:
            items = Post.objects.filter(topic__forum__id=obj.id)
        return items.order_by('-creation_date').select_related()[:10]

    def item_pubdate(self, item):
       return item.creation_date

    def item_categories(self, item):
       return (item.topic.forum.name, )
