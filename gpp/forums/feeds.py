"""This file contains the feed class for the forums application."""

from django.contrib.syndication.views import Feed
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from forums.models import Forum, Topic, Post
from core.functions import copyright_str


class ForumsFeed(Feed):
    """The Feed class for a specific forum"""

    ttl = '60'
    author_name = 'Brian Neal'
    author_email = 'admin@surfguitar101.com'

    def get_object(self, request, forum_slug):
        # only return public forums
        if forum_slug:
            forum = get_object_or_404(Forum, slug=forum_slug)
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
        if obj is None:
            # return a combined feed of public forum threads

            # This was tricky to do without suffering a large performance
            # impact. Because the number of forums is small, MySQL did not
            # try to use an index and ended up searching all the topics for
            # candidate posts. We work around this by first getting a small list
            # of candidate topics, and then searching them. This is more
            # queries but a *lot* more time efficient.

            forum_ids = Forum.objects.public_forum_ids()
            topic_ids = list(Topic.objects.filter(forum__in=forum_ids).order_by(
                    '-update_date').values_list('id', flat=True)[:30])
            items = Post.objects.filter(topic__in=topic_ids)

        else:
            items = Post.objects.filter(topic__forum=obj)

        return items.order_by('-creation_date').select_related('topic', 'user',
                'topic__forum')[:30]

    def item_title(self, item):
        return item.topic.name

    def item_description(self, item):
        return item.html

    def item_author_name(self, item):
        return item.user.username

    def item_pubdate(self, item):
       return item.creation_date

    def item_categories(self, item):
       return (item.topic.forum.name, )
