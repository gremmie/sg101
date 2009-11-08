"""
This file contains the automatic admin site definitions for the Smiley models.
"""

from django.contrib import admin
from smiley.models import Smiley

class SmileyAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'html', 'is_extra')

admin.site.register(Smiley, SmileyAdmin)
