'''
This file contains the automatic admin site definitions for the Bulletins models.
'''

from django.contrib import admin
from django.conf import settings

from bulletins.models import Bulletin

class BulletinAdmin(admin.ModelAdmin):
   list_display = ('title', 'start_date', 'end_date', 'is_enabled')
   list_filter = ('start_date', 'end_date', 'is_enabled')
   search_fields = ('title', 'text')
   date_hierarchy = 'start_date'

   class Media:
      js = settings.GPP_THIRD_PARTY_JS['tiny_mce']


admin.site.register(Bulletin, BulletinAdmin)
