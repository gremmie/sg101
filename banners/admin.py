"""
This file contains the automatic admin site definitions for the banners models.

"""
from django.contrib import admin

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
        return '<img src="%s" alt="%s" />' % (obj.image.url, obj.description)
    image_tag.allow_tags = True

admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Banner, BannerAdmin)
