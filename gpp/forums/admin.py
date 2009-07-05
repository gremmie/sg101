"""
This file contains the admin definitions for the forums application.
"""
from django.contrib import admin

from forums.models import Category
from forums.models import Forum
from forums.models import Topic
from forums.models import Post


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', )


class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'position', 'topic_count', 'post_count')
    prepopulated_fields = { 'slug': ('name', ) }
    raw_id_fields = ('last_post', )

class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'forum', 'creation_date', 'user', 'sticky', 'locked',
            'post_count')
    raw_id_fields = ('user', 'last_post', )
    search_fields = ('name', )
    date_hierarchy = 'creation_date'
    list_filter = ('creation_date', 'update_date', )


class PostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'creation_date', 'update_date', 'summary')
    raw_id_fields = ('topic', 'user', )
    exclude = ('html', )
    search_fields = ('body', )
    date_hierarchy = 'creation_date'
    list_filter = ('creation_date', 'update_date', )


admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
