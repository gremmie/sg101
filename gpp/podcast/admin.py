'''
This file contains the automatic admin site definitions for the podcast models.
'''

from django.contrib import admin
from podcast.models import Channel
from podcast.models import Item


class ItemInline(admin.StackedInline):
   model = Item
   extra = 1


class ChannelAdmin(admin.ModelAdmin):
   inlines = (ItemInline, )


admin.site.register(Channel, ChannelAdmin)
