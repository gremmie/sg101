"""
This file contains the admin definitions for the forums application.
"""
from django.contrib import admin

from forums.models import Category
from forums.models import Forum
from forums.models import Topic
from forums.models import Post
from forums.models import FlaggedPost
from forums.models import ForumLastVisit
from forums.models import TopicLastVisit
import bio.badges


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', )
    list_editable = ('position', )
    prepopulated_fields = { 'slug': ('name', ) }
    save_on_top = True


class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'position', 'topic_count', 'post_count')
    list_editable = ('position', )
    prepopulated_fields = { 'slug': ('name', ) }
    raw_id_fields = ('last_post', )
    ordering = ('category', )
    save_on_top = True


class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'forum', 'creation_date', 'update_date', 'user', 'sticky', 'locked',
            'post_count')
    raw_id_fields = ('user', 'last_post', 'subscribers', 'bookmarkers')
    search_fields = ('name', )
    date_hierarchy = 'creation_date'
    list_filter = ('creation_date', 'update_date', )
    save_on_top = True


class PostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'creation_date', 'update_date', 'summary')
    raw_id_fields = ('topic', 'user', )
    exclude = ('html', )
    search_fields = ('body', )
    date_hierarchy = 'creation_date'
    list_filter = ('creation_date', 'update_date', )
    ordering = ('-creation_date', )
    save_on_top = True


class FlaggedPostAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'flag_date', 'get_post_url')
    actions = ('accept_flags', )

    def accept_flags(self, request, qs):
        """This admin action awards a security pin to the user who reported
        the post and then deletes the flagged post object.
        """
        for flag in qs:
            bio.badges.award_badge(bio.badges.SECURITY_PIN, flag.user)
            flag.delete()

    accept_flags.short_description = "Accept selected flagged posts"


class ForumLastVisitAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'forum')
    list_display = ('user', 'forum', 'begin_date', 'end_date')


class TopicLastVisitAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'topic')
    list_display = ('user', 'topic', 'last_visit')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(FlaggedPost, FlaggedPostAdmin)
admin.site.register(ForumLastVisit, ForumLastVisitAdmin)
admin.site.register(TopicLastVisit, TopicLastVisitAdmin)
