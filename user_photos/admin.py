"""Admin definitions for the user_photos application."""
from django.contrib import admin
from django.utils.html import format_html

from user_photos.models import Photo
from user_photos.s3 import delete_photos

IMG_TAG = """<a href="{url}"><img src="{thumb_url}" alt="thumbnail" /></a>"""

class PhotoAdmin(admin.ModelAdmin):
    date_hierarchy = 'upload_date'
    ordering = ['-upload_date']
    raw_id_fields = ['user']
    search_fields = ['user__username', 'user__email']
    list_display = ['__unicode__', 'thumbnail']
    actions = ['custom_delete']

    def thumbnail(self, obj):
        return format_html(IMG_TAG, url=obj.url, thumb_url=obj.thumb_url)

    def custom_delete(self, request, qs):
        """Custom delete in order to remove images from the S3 bucket in
        addition to removing from the database.

        """
        delete_photos(qs)
        count = len(qs)
        qs.delete()

        if count == 1:
            msg_bit = "1 photo was"
        else:
            msg_bit = "{} photos were".format(count)

        self.message_user(request, "{} successfully deleted.".format(msg_bit))
    custom_delete.short_description = "Delete selected photos from DB & S3"

    def get_actions(self, request):
        """Remove the default delete selected action because we have installed
        our own.

        """
        actions = super(PhotoAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions


admin.site.register(Photo, PhotoAdmin)
