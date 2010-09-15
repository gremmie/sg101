"""
This file contains the automatic admin site definitions for the News models.
"""
import datetime

from django.contrib import admin
from django.conf import settings

from news.models import PendingStory
from news.models import Story
from news.models import Category


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("title", )}
    list_display = ('title', 'slug')


class PendingStoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_submitted', 'submitter')
    list_filter = ('date_submitted', )
    search_fields = ('title', 'short_text', 'long_text')
    date_hierarchy = 'date_submitted'
    actions = ('approve_story', )

    def approve_story(self, request, qs):
        for pending_story in qs:
            story = Story(
                    title=pending_story.title,
                    submitter=pending_story.submitter,
                    category=pending_story.category,
                    short_text=pending_story.short_text,
                    long_text=pending_story.long_text,
                    date_submitted=datetime.datetime.now(),
                    allow_comments=pending_story.allow_comments,
                    tags=pending_story.tags,
                    front_page_expiration=pending_story.front_page_expiration)
            story.save()
            pending_story.delete()

    approve_story.short_description = "Approve selected pending stories"

    class Media:
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']


class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_submitted', 'submitter', 'category')
    list_filter = ('date_submitted', 'category')
    search_fields = ('title', 'short_text', 'long_text')
    date_hierarchy = 'date_submitted'

    class Media:
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(PendingStory, PendingStoryAdmin)
