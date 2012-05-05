"""This file contains the automatic admin site definitions for the weblinks models"""
import datetime

from django.contrib import admin
from weblinks.models import Category
from weblinks.models import PendingLink
from weblinks.models import Link
from weblinks.models import FlaggedLink


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description', 'count')
    prepopulated_fields = {'slug': ('title', )}
    readonly_fields = ('count', )


class PendingLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'user', 'category', 'date_added')
    raw_id_fields = ('user', )
    actions = ('approve_links', )
    readonly_fields = ('update_date', )

    def approve_links(self, request, qs):
        for pending_link in qs:
            link = Link(category=pending_link.category,
                    title=pending_link.title,
                    url=pending_link.url,
                    description=pending_link.description,
                    user=pending_link.user,
                    date_added=datetime.datetime.now(),
                    hits=0,
                    is_public=True)
            link.save()
            pending_link.delete()

        count = len(qs)
        msg = "1 link" if count == 1 else "%d links" % count
        self.message_user(request, "%s approved." % msg)

    approve_links.short_description = "Approve selected links"


class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'category', 'date_added', 'hits', 'is_public')
    list_filter = ('date_added', 'is_public', 'category')
    date_hierarchy = 'date_added'
    ordering = ('-date_added', )
    search_fields = ('title', 'description', 'url', 'user__username')
    raw_id_fields = ('user', )
    readonly_fields = ('update_date', )
    save_on_top = True


class FlaggedLinkAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'url', 'get_link_url', 'user', 'date_flagged')
    date_hierarchy = 'date_flagged'
    raw_id_fields = ('user', )

admin.site.register(Category, CategoryAdmin)
admin.site.register(PendingLink, PendingLinkAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(FlaggedLink, FlaggedLinkAdmin)
