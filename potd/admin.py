"""
This file contains the admin definitions for the POTD application.
"""
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from potd.models import Photo
from potd.models import Current
from potd.models import Sequence


IMG_TAG = '<img src="{}" alt="thumbnail" />'


class PhotoAdmin(admin.ModelAdmin):
    fields = ['photo', 'caption', 'description', 'user', 'potd_count']
    raw_id_fields = ['user']
    list_display = ['__unicode__', 'thumbnail']
    actions = ['regen_thumbnail']
    search_fields = ['caption', 'description']

    class Media:
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']

    def thumbnail(self, obj):
        return format_html(IMG_TAG, obj.thumb.url)

    def regen_thumbnail(self, request, qs):
        """
        Regenerates the thumbnail for the selected photos.
        """
        for photo in qs:
            photo.generate_thumb()
            photo.save()

    regen_thumbnail.short_description = "Regenerate thumbs for selected photos"


class CurrentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'thumbnail')
    raw_id_fields = ('potd', )

    def thumbnail(self, obj):
        return format_html(IMG_TAG, obj.potd.thumb.url)


admin.site.register(Photo, PhotoAdmin)
admin.site.register(Current, CurrentAdmin)
admin.site.register(Sequence)
