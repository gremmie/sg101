"""
This file contains the automatic admin site definitions for the shoutbox models.
"""
from django.contrib import admin
from shoutbox.models import Shout

class ShoutAdmin(admin.ModelAdmin):
   list_display = ('shout_date', '__unicode__')
   raw_id_fields = ('user', )

admin.site.register(Shout, ShoutAdmin)
