"""
This file contains the automatic admin site definitions for the News models.
"""

from django.contrib import admin
from news.models import PendingStory
from news.models import Story
from news.models import Category

class PendingStoryAdmin(admin.ModelAdmin):
   list_display = ('title', 'date_submitted', 'submitter')
   list_filter = ('date_submitted', )
   search_fields = ('title', 'short_text', 'long_text')
   date_hierarchy = 'date_submitted'

   class Media:
      js = ('js/tiny_mce/tiny_mce.js', 'js/tiny_mce_init_admin.js')


class StoryAdmin(admin.ModelAdmin):
   list_display = ('title', 'date_published', 'submitter', 'category')
   list_filter = ('date_published', 'category')
   search_fields = ('title', 'short_text', 'long_text')
   date_hierarchy = 'date_published'

   class Media:
      js = ('js/tiny_mce/tiny_mce.js', 'js/tiny_mce_init_admin.js')


admin.site.register(Category)
admin.site.register(Story, StoryAdmin)
admin.site.register(PendingStory, PendingStoryAdmin)
