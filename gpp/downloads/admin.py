"""
This file contains the automatic admin site definitions for the downloads models.
"""
import datetime

from django.contrib import admin
from django.conf import settings

from downloads.models import PendingDownload
from downloads.models import Download
from downloads.models import Category
from downloads.models import AllowedExtension
from downloads.models import VoteRecord


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description', 'count')
    prepopulated_fields = {'slug': ('title', )}
    readonly_fields = ('count', )


class PendingDownloadAdmin(admin.ModelAdmin):
    exclude = ('html', )
    list_display = ('title', 'user', 'category', 'date_added', 'ip_address', 'size')
    ordering = ('date_added', )
    raw_id_fields = ('user', )
    readonly_fields = ('update_date', )

    actions = ('approve_downloads', )

    def approve_downloads(self, request, qs):
        for pending_dl in qs:
            dl = Download(
                    title=pending_dl.title,
                    category=pending_dl.category,
                    description=pending_dl.description,
                    html=pending_dl.html,
                    file=pending_dl.file,
                    user=pending_dl.user,
                    date_added=datetime.datetime.now(),
                    ip_address=pending_dl.ip_address,
                    hits=0,
                    average_score=0.0,
                    total_votes=0,
                    is_public=True)
            dl.save()

            # If we don't do this, the actual file will be deleted when
            # the pending download is deleted.
            pending_dl.file = None
            pending_dl.delete()

    approve_downloads.short_description = "Approve selected downloads"


class DownloadAdmin(admin.ModelAdmin):
    exclude = ('html', )
    list_display = ('title', 'user', 'category', 'date_added', 'ip_address',
               'hits', 'average_score', 'size', 'is_public')
    list_filter = ('date_added', 'is_public', 'category', 'user', 'ip_address')
    date_hierarchy = 'date_added'
    ordering = ('-date_added', )
    search_fields = ('title', 'description', 'user__username')
    raw_id_fields = ('user', )
    readonly_fields = ('update_date', )
    save_on_top = True


class VoteRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'download', 'vote_date')
    list_filter = ('user', 'download')
    date_hierarchy = 'vote_date'


admin.site.register(PendingDownload, PendingDownloadAdmin)
admin.site.register(Download, DownloadAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(AllowedExtension)
admin.site.register(VoteRecord, VoteRecordAdmin)

