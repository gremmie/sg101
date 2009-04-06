"""
This file contains the automatic admin site definitions for the downloads models.
"""
from django.contrib import admin
from downloads.models import Download
from downloads.models import Category
from downloads.models import AllowedExtension
from downloads.models import VoteRecord

class DownloadAdmin(admin.ModelAdmin):
    exclude = ('html', )
    list_display = ('title', 'user', 'category', 'date_added', 'ip_address',
            'hits', 'average_score', 'size', 'is_public')
    list_filter = ('date_added', 'is_public', 'category', 'user', 'ip_address')
    date_hierarchy = 'date_added'
    ordering = ('-date_added', )
    search_fields = ('title', 'description', 'user__username')
    raw_id_fields = ('user', )
    save_on_top = True

    class Media:
        css = {
            'all': ('js/markitup/skins/markitup/style.css',
                    'js/markitup/sets/markdown/style.css')
        }
        js = (
            'js/jquery-1.2.6.min.js',
            'js/markitup/jquery.markitup.pack.js',
            'js/markitup/sets/markdown/set.js',
            'js/downloads_admin.js',
        )


class VoteRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'download', 'vote_date')
    list_filter = ('user', 'download')
    date_hierarchy = 'vote_date'


admin.site.register(Download, DownloadAdmin)
admin.site.register(Category)
admin.site.register(AllowedExtension)
admin.site.register(VoteRecord, VoteRecordAdmin)
