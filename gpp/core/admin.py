"""This file contains the automatic admin site definitions for the core Models"""

from django.contrib import admin
from core.models import DebugLog

class DebugLogAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'level')
    ordering = ('-timestamp', )
    date_hierarchy = 'timestamp'

admin.site.register(DebugLog, DebugLogAdmin)

# vim: ts=4 sw=4
