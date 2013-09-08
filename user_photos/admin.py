"""Admin definitions for the user_photos application."""
from django.contrib import admin

from user_photos.models import Photo


class PhotoAdmin(admin.ModelAdmin):
    date_hierarchy = 'upload_date'
    ordering = ['-upload_date']
    raw_id_fields = ['user']
    search_fields = ['user__username', 'user__email']

admin.site.register(Photo, PhotoAdmin)
