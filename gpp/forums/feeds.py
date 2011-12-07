"""
This file contains the feed class for the forums application.

"""
from django.contrib.syndication.views import Feed
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from forums.models import Forum, Topic, Post
from core.functions import copyright_str
from forums.latest import get_latest_posts


class ForumsFeed(Feed):
    """The Feed class for a specific forum"""

    ttl = '60'
    author_name = 'Brian Neal'
    author_email = 'admin@surfguitar101.com'

    def get_object(self, request, forum_slug):

        if forum_slug:
            forum = Forum.objects.get(slug=forum_slug)
            # only return public forums
            if forum.id not in Forum.objects.public_forum_ids():
                raise ObjectDoesNotExist
            return forum

        else:
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

    def feed_copyright(self):
        return copyright_str()

    def items(self, obj):
        forum_id = obj.id if obj else None
        return get_latest_posts(forum_id=forum_id)

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return item['content']

    def item_author_name(self, item):
        return item['author']

    def item_pubdate(self, item):
        return item['pubdate']

    def item_categories(self, item):
        return [item['forum_name']]

    def item_link(self, item):
        return item['url']
