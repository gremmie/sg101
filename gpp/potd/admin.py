"""
This file contains the admin definitions for the POTD application.
"""
from django.contrib import admin
from django.conf import settings

from potd.models import Photo
from potd.models import Current
from potd.models import Sequence


class PhotoAdmin(admin.ModelAdmin):
    exclude = ('thumb', )
    raw_id_fields = ('user', )

    class Media:
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']

class CurrentAdmin(admin.ModelAdmin):
    raw_id_fields = ('potd', )

admin.site.register(Photo, PhotoAdmin)
admin.site.register(Current, CurrentAdmin)
admin.site.register(Sequence)
