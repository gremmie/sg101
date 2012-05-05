"""
Admin site definitions for the oembed application.
"""
from django.contrib import admin

from oembed.models import Provider
from oembed.models import Oembed


class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_endpoint', 'format')
    list_filter = ('format', )
    search_fields = ('name', )


class OembedAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_added'
    list_display = ('__unicode__', 'type', 'url', 'date_added')
    list_filter = ('type', )
    search_fields = ('title', )


admin.site.register(Provider, ProviderAdmin)
admin.site.register(Oembed, OembedAdmin)
