"""
This file contains the automatic admin site definitions for the News models.
"""
from django.contrib import admin
from django.conf import settings

from news.models import PendingStory
from news.models import Story
from news.models import Category

import ftfy


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("title", )}
    list_display = ['title', 'slug']


class PendingStoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'date_submitted', 'submitter']
    list_filter = ['date_submitted']
    search_fields = ['title', 'short_text', 'long_text']
    date_hierarchy = 'date_submitted'
    actions = ['approve_story']
    readonly_fields = ['update_date']
    raw_id_fields = ['submitter']

    def approve_story(self, request, qs):
        for pending_story in qs:
            story = Story(
                    title=pending_story.title,
                    submitter=pending_story.submitter,
                    category=pending_story.category,
                    short_text=pending_story.short_text,
                    long_text=pending_story.long_text,
                    date_submitted=pending_story.date_submitted,
                    allow_comments=pending_story.allow_comments,
                    tags=pending_story.tags,
                    front_page_expiration=pending_story.front_page_expiration,
                    priority=pending_story.priority,
                    meta_description=pending_story.meta_description)
            story.save()
            pending_story.delete()

        count = len(qs)
        msg = "1 story" if count == 1 else "%d stories" % count
        self.message_user(request, "%s approved." % msg)

    approve_story.short_description = "Approve selected pending stories"

    class Media:
        js = ['js/news_admin.js'] + settings.GPP_THIRD_PARTY_JS['tiny_mce']


class StoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'date_submitted', 'submitter', 'category']
    list_filter = ['date_submitted', 'category']
    search_fields = ['title', 'short_text', 'long_text']
    date_hierarchy = 'date_submitted'
    readonly_fields = ['update_date']
    raw_id_fields = ['submitter']
    actions = ['fix_text']

    def fix_text(self, request, qs):
        for story in qs:
            story.title = ftfy.fix_text(story.title)
            story.short_text = ftfy.fix_text(story.short_text)
            story.long_text = ftfy.fix_text(story.long_text)
            story.save()

        count = len(qs)
        msg = "1 story" if count == 1 else "%d stories" % count
        self.message_user(request, "Text fixed on {}".format(msg))

    fix_text.short_description = "Fix text on selected stories"

    class Media:
        js = ['js/news_admin.js'] + settings.GPP_THIRD_PARTY_JS['tiny_mce']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(PendingStory, PendingStoryAdmin)
