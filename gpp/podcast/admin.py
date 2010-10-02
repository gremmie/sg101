'''
This file contains the automatic admin site definitions for the podcast models.
'''

from django.contrib import admin
from podcast.models import Channel
from podcast.models import Item

class ItemAdmin(admin.ModelAdmin):
    readonly_fields = ('update_date', )

admin.site.register(Channel)
admin.site.register(Item, ItemAdmin)
