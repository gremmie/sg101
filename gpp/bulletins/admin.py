'''
This file contains the automatic admin site definitions for the Bulletins models.
'''

from django.contrib import admin
from bulletins.models import Bulletin

class BulletinAdmin(admin.ModelAdmin):
   list_display = ('title', 'start_date', 'end_date', 'is_enabled')
   list_filter = ('start_date', 'end_date', 'is_enabled')
   search_fields = ('title', 'text')
   date_hierarchy = 'start_date'

   class Media:
      js = ('js/tiny_mce/tiny_mce.js', 'js/tiny_mce_init_admin.js')


admin.site.register(Bulletin, BulletinAdmin)
