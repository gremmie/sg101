"""
This file contains the automatic admin site definitions for the comment models.
"""
from django.contrib import admin
from comments.models import Comment
from comments.models import CommentFlag

class CommentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type', 'object_id', )}
        ),
        ('Content',
           {'fields': ('user', 'comment')}
        ),
        ('Metadata',
           {'fields': ('ip_address', 'is_public', 'is_removed')}
        ),
     )
    list_display = ('__unicode__', 'content_type', 'object_id', 'ip_address', 'creation_date', 'is_public', 'is_removed')
    list_filter = ('creation_date', 'is_public', 'is_removed')
    date_hierarchy = 'creation_date'
    ordering = ('-creation_date', )
    search_fields = ('comment', 'user__username', 'ip_address')
    raw_id_fields = ('user', 'content_type')

class CommentFlagAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'flag_date', 'get_comment_url')

admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentFlag, CommentFlagAdmin)
