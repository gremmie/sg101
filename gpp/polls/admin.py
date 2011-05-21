'''
This file contains the automatic admin site definitions for the polls models.
'''

from django.contrib import admin
from polls.models import Poll
from polls.models import Choice


class ChoiceInline(admin.TabularInline):
   model = Choice
   extra = 3
   raw_id_fields = ['voters']


class PollAdmin(admin.ModelAdmin):
   list_display = ['question', 'start_date', 'end_date', 'is_enabled']
   inlines = [ChoiceInline]
   list_filter = ['start_date', 'end_date']
   search_fields = ['question']
   date_hierarchy = 'start_date'


admin.site.register(Poll, PollAdmin)
