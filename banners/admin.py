"""
This file contains the automatic admin site definitions for the banners models.

"""
from django.contrib import admin
from django.utils.html import format_html

from banners.models import Campaign, Banner


class BannerInline(admin.TabularInline):
    model = Banner
    extra = 1


class CampaignAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['name']}
    list_display = ['name', 'slug', 'creation_date']
    date_hierarchy = 'creation_date'
    search_fields = ['name']
    inlines = [BannerInline]


class BannerAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'description', 'image_tag', 'creation_date']
    date_hierarchy = 'creation_date'
    search_fields = ['description']
    list_filter = ['campaign']

    def image_tag(self, obj):
        return format_html('<img src="{}" alt="{}" />', obj.image.url, obj.description)

admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Banner, BannerAdmin)
