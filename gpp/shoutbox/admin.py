"""
This file contains the automatic admin site definitions for the shoutbox models.
"""
from django.contrib import admin
from shoutbox.models import Shout
from shoutbox.models import ShoutFlag

class ShoutAdmin(admin.ModelAdmin):
    list_display = ('shout_date', '__unicode__')
    raw_id_fields = ('user', )

class ShoutFlagAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'flag_date', 'get_shout_url')


admin.site.register(Shout, ShoutAdmin)
admin.site.register(ShoutFlag, ShoutFlagAdmin)

# vim: ts=4 sw=4
