"""This file contains the automatic admin site definitions for the weblinks models"""

from django.contrib import admin
from weblinks.models import Category
from weblinks.models import Link
from weblinks.models import FlaggedLink

class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'category', 'date_added', 'hits', 'is_public')
    list_filter = ('date_added', 'is_public', 'category')
    date_hierarchy = 'date_added'
    ordering = ('-date_added', )
    search_fields = ('title', 'description', 'url', 'user__username')
    raw_id_fields = ('user', )
    save_on_top = True

class FlaggedLinkAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'url', 'date_flagged')
    date_hierarchy = 'date_flagged'
    raw_id_fields = ('user', )

admin.site.register(Category)
admin.site.register(Link, LinkAdmin)
admin.site.register(FlaggedLink, FlaggedLinkAdmin)
