"""
This file contains the automatic admin site definitions for the News models.
"""
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextInputWidget
from django.contrib.postgres.fields import ArrayField
from django.conf import settings

from core.admin import PlainTextFieldsMixin

from forums.tools import create_topic
from news.models import PendingStory
from news.models import Story
from news.models import Category

import ftfy


COMMENT_THREAD_BODY = (u"This topic was automatically created to discuss the "
        u"news story [{title}]({url}).")

# An ArrayField's form field wraps a plain TextInput, which never picks up the
# class the admin styles its text inputs with -- so the tag box renders at the
# browser default of about twenty characters. One story carries 251 characters
# of tags, so it is given the row instead.
TAG_FIELD_OVERRIDES = {
    ArrayField: {
        'widget': AdminTextInputWidget(attrs={'style': 'width: 100%'}),
    },
}


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("title", )}
    list_display = ['title', 'slug', 'forum_slug']
    list_editable = ['forum_slug']


class PendingStoryAdmin(PlainTextFieldsMixin, admin.ModelAdmin):
    formfield_overrides = TAG_FIELD_OVERRIDES
    plain_text_fields = ['short_markup', 'long_markup', 'meta_description']
    list_display = ['title', 'date_submitted', 'submitter']
    list_filter = ['date_submitted']
    search_fields = ['title', 'short_text', 'long_text']
    date_hierarchy = 'date_submitted'
    actions = ['approve_stories']
    readonly_fields = ['update_date', 'version']
    raw_id_fields = ['submitter']

    fieldsets = [
        (None, {
            'fields': ['title', 'submitter', 'category'],
            }),
        ('New Markdown Fields', {
            'fields': ['short_markup', 'long_markup'],
            }),
        ('HTML Fields', {
            'fields': ['short_text', 'long_text', 'admin_content'],
            'classes': ['collapse'],
            }),
        ('Meta Fields', {
            'fields': [
                'date_submitted', 'allow_comments', 'tags',
                'front_page_expiration', 'priority', 'meta_description',
                ]
            }),
        ('Read-Only Fields', {
            'fields': ['update_date', 'version'],
            'classes': ['collapse'],
            }),
    ]

    def approve_stories(self, request, qs):
        for pending_story in qs:
            self._approve_story(pending_story)

        count = len(qs)
        msg = "1 story" if count == 1 else "%d stories" % count
        self.message_user(request, "%s approved." % msg)

    approve_stories.short_description = "Approve selected pending stories"

    def _approve_story(self, pending_story):
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
                meta_description=pending_story.meta_description,
                short_markup=pending_story.short_markup,
                long_markup=pending_story.long_markup,
                admin_content=pending_story.admin_content,
                version=pending_story.version)
        story.save()
        pending_story.delete()

        # Create comment thread if configured to do so.
        forum_slug = story.category.forum_slug
        if story.allow_comments and forum_slug:
            post_body = COMMENT_THREAD_BODY.format(title=story.title,
                                                   url=story.get_absolute_url())
            topic = create_topic(forum_slug, story.submitter, story.title, post_body)
            story.forums_topic = topic
            story.save()

    class Media:
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']


class StoryAdmin(PlainTextFieldsMixin, admin.ModelAdmin):
    formfield_overrides = TAG_FIELD_OVERRIDES
    plain_text_fields = PendingStoryAdmin.plain_text_fields
    list_display = ['title', 'date_submitted', 'submitter', 'category']
    list_filter = ['date_submitted', 'category']
    search_fields = ['title', 'short_text', 'long_text']
    date_hierarchy = 'date_submitted'
    readonly_fields = ['update_date', 'version']
    raw_id_fields = ['submitter', 'forums_topic']
    actions = ['fix_text']

    fieldsets = PendingStoryAdmin.fieldsets + [
        ('Comments', {
            'fields': ['forums_topic'],
            })
    ]

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
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(PendingStory, PendingStoryAdmin)
