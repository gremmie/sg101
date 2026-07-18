"""
This file contains the automatic admin site definitions for the shoutbox models.
"""
from django.contrib import admin
from shoutbox.models import Shout
from shoutbox.models import ShoutFlag

class ShoutAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'shout_date')
    raw_id_fields = ('user', )
    date_hierarchy = 'shout_date'
    exclude = ('html', )
    search_fields = ('shout', 'user__username')
    list_filter = ('shout_date', )


class ShoutFlagAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'flag_date', 'shout', 'get_shout_url')
    actions = ('delete_shouts', )

    def delete_shouts(self, request, qs):
        """
        Admin action function to delete the shouts associated with the shout
        flags.
        """
        for flag in qs:
            flag.shout.delete()     # will delete the flag too

    delete_shouts.short_description = "Delete selected flags & shouts"


admin.site.register(Shout, ShoutAdmin)
admin.site.register(ShoutFlag, ShoutFlagAdmin)

