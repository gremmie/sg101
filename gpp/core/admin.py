"""This file contains the automatic admin site definitions for the core Models"""

from django.contrib import admin
from core.models import SiteConfig
from core.models import DebugLog

class SiteConfigAdmin(admin.ModelAdmin):
   pass

class DebugLogAdmin(admin.ModelAdmin):
   list_display = ('__unicode__', 'level')
   ordering = ('-timestamp', )
   date_hierarchy = 'timestamp'

admin.site.register(SiteConfig, SiteConfigAdmin)
admin.site.register(DebugLog, DebugLogAdmin)
