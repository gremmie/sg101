"""Admin definitions for the user_photos application."""
from django.contrib import admin

from user_photos.models import Photo

IMG_TAG = """<a href="{url}"><img src="{thumb_url}" alt="thumbnail" /></a>"""

class PhotoAdmin(admin.ModelAdmin):
    date_hierarchy = 'upload_date'
    ordering = ['-upload_date']
    raw_id_fields = ['user']
    search_fields = ['user__username', 'user__email']
    list_display = ['__unicode__', 'thumbnail']

    def thumbnail(self, obj):
        return IMG_TAG.format(url=obj.url, thumb_url=obj.thumb_url)
    thumbnail.allow_tags = True

admin.site.register(Photo, PhotoAdmin)
